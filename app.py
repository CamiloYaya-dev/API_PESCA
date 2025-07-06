from flask import Flask, request, jsonify
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_KEY_ESPERADA = os.getenv("API_KEY")
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

@app.route("/validar", methods=["POST"])
def validar_licencia():
    api_key = request.headers.get("x-api-key")
    data = request.json

    if not api_key or api_key != API_KEY_ESPERADA:
        return jsonify({"status": "error", "mensaje": "API key inválida"}), 401

    clave = data.get("clave")
    if not clave:
        return jsonify({"status": "error", "mensaje": "Falta la clave"}), 400

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT usuario FROM licencias WHERE clave=%s AND activa=1", (clave,))
        fila = cursor.fetchone()
        cursor.close()
        conn.close()
    except Exception as e:
        return jsonify({"status": "error", "mensaje": f"Error en base de datos: {str(e)}"}), 500

    if fila:
        return jsonify({"status": "valido", "usuario": fila["usuario"]})
    else:
        return jsonify({"status": "invalido", "mensaje": "Llave no autorizada o expirada"})

if __name__ == "__main__":
    app.run(port=5000)
