from flask import Flask, request, jsonify, send_file
import mysql.connector
import os
import json
from dotenv import load_dotenv

app = Flask(__name__)

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración desde entorno
API_KEY = os.getenv("API_KEY")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "licencias_bot")

# Archivos a servir
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

IMG_PATH = os.path.join(BASE_DIR, "archivos", "3ZuxE7bre0kypSqM76n5dkak7zZBu0")
ZIP_PATH = os.path.join(BASE_DIR, "archivos", "archivos_origins.zip")

def validar_api_key(api_key):
    return api_key == API_KEY

@app.route("/validar", methods=["POST"])
def validar_licencia():
    api_key = request.headers.get("x-api-key")
    data = request.json

    if not api_key or not validar_api_key(api_key):
        return jsonify({"status": "error", "mensaje": "API key inválida"}), 401

    clave = data.get("clave")
    if not clave:
        return jsonify({"status": "error", "mensaje": "Falta la clave"}), 400

    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT usuario FROM licencias WHERE clave=%s AND activa=1", (clave,))
    fila = cursor.fetchone()
    cursor.close()
    conn.close()

    if fila:
        return jsonify({"status": "valido", "usuario": fila["usuario"]})
    else:
        return jsonify({"status": "invalido", "mensaje": "Llave no autorizada o expirada"})

@app.route("/descargar/img", methods=["GET"])
def descargar_img():
    api_key = request.headers.get("x-api-key")
    if not api_key or not validar_api_key(api_key):
        return jsonify({"status": "error", "mensaje": "API key inválida"}), 401

    if not os.path.exists(IMG_PATH):
        return jsonify({"status": "error", "mensaje": "Archivo no encontrado"}), 404

    return send_file(IMG_PATH, as_attachment=True)

@app.route("/descargar/zip", methods=["GET"])
def descargar_zip():
    api_key = request.headers.get("x-api-key")
    if not api_key or not validar_api_key(api_key):
        return jsonify({"status": "error", "mensaje": "API key inválida"}), 401

    if not os.path.exists(ZIP_PATH):
        return jsonify({"status": "error", "mensaje": "Archivo no encontrado"}), 404

    return send_file(ZIP_PATH, as_attachment=True)

@app.route("/actualizar", methods=["GET"])
def verificar_actualizacion():
    try:
        update_file = os.getenv("UPDATE_FILE", "./actualizacion.json")
        with open(update_file, "r", encoding="utf-8") as f:
            archivos = json.load(f)
        if not archivos:
            return "", 205
        return jsonify(archivos)
    except Exception as e:
        return jsonify({"status": "error", "mensaje": f"Error leyendo archivo de actualización: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(port=5000)