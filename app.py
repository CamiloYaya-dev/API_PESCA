from flask import Flask, request, jsonify, send_file, Response
import mysql.connector
import os
import json
from dotenv import load_dotenv
import logging

app = Flask(__name__)

load_dotenv()

API_KEY = os.getenv("API_KEY")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ZIP_PATH = os.path.join(BASE_DIR, "archivos", "archivos_origins.zip")

def validar_api_key(api_key):
    return api_key == API_KEY

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "validaciones.log")),
        logging.StreamHandler()
    ]
)

@app.route("/validar", methods=["POST"])
def validar_licencia():
    try:
        api_key = request.headers.get("x-api-key")
        data = request.get_json(force=True)
        ip = request.remote_addr

        logging.info("Solicitud /validar desde IP %s", ip)
        logging.info("Headers: %s", dict(request.headers))
        logging.info("Body recibido: %s", data)

        if not api_key:
            logging.warning("API key ausente desde IP %s", ip)
            return jsonify({"status": "error", "mensaje": "API key inválida"}), 401

        if not validar_api_key(api_key):
            logging.warning("API key inválida '%s' desde IP %s", api_key, ip)
            return jsonify({"status": "error", "mensaje": "API key inválida"}), 401

        clave = data.get("clave")
        if not clave:
            logging.warning("Clave ausente desde IP %s", ip)
            return jsonify({"status": "error", "mensaje": "Falta la clave"}), 400

        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
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
            logging.info("✅ Licencia válida para usuario '%s' desde IP %s", fila["usuario"], ip)
            return jsonify({"status": "valido", "usuario": fila["usuario"]})
        else:
            logging.info("🚫 Licencia inválida '%s' desde IP %s", clave, ip)
            return jsonify({"status": "invalido", "mensaje": "Llave no autorizada o expirada"})

    except Exception as e:
        logging.exception("💥 Error inesperado al procesar /validar desde IP %s: %s", request.remote_addr, str(e))
        return jsonify({"status": "error", "mensaje": "Error interno del servidor"}), 500
    
def generar_stream(path, chunk_size=16*1024*1024):
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk

@app.route("/descargar/img", methods=["GET"])
def descargar_img():
    api_key = request.headers.get("x-api-key")
    if not api_key or not validar_api_key(api_key):
        return jsonify({"status": "error", "mensaje": "API key inválida"}), 401

    nombre_archivo = "3ZuxE7bre0kypSqM76n5dkak7zZBu0"
    ruta_nginx = f"/archivos_privados/{nombre_archivo}"
    return Response(
        status=200,
        headers={
            "Content-Disposition": f"attachment; filename={nombre_archivo}",
            "X-Accel-Redirect": ruta_nginx,
            "Content-Type": "application/octet-stream"
        }
    )

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

@app.route("/__version__")
def version():
    return jsonify({"versión": "7-julio-2025", "estado": "ok"})

if __name__ == "__main__":
    app.run(port=5000, threaded=True)
