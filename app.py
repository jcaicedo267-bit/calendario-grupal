from flask import Flask, render_template, request, jsonify
import json 
import os

app = Flask(__name__)

ARCHIVO_DATOS = 'eventos.json'

def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, 'r') as f:
            return json.load(f)
    return []

def guardar_datos(datos):
    with open(ARCHIVO_DATOS, 'w') as f:
        json.dump(datos, f, indent=4)

        
@app.route("/")
def inicio():
    return render_template("index.html")
    


eventos = []

@app.route("/api/eventos", methods=["GET", "POST"])
def manejar_eventos():
    if request.method == "POST":
        nuevo_evento = request.json
        eventos.append(nuevo_evento)
        return jsonify({"mensaje": "Evento guardado"}), 201
    return jsonify(eventos)

if __name__ == "__main__":
    app.run(debug=True)