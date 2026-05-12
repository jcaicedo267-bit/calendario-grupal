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
    return render_template("principal.html")

@app.route("/api/eventos", methods=["GET", "POST"])
def manejar_eventos():
    eventos = cargar_datos()
    if request.method == "POST":
        nuevo_evento = request.json
        eventos.append(nuevo_evento)
        guardar_datos(eventos)
        return jsonify({"mensaje": "Evento guardado correctamente"}), 201
    return jsonify(eventos)

@app.route("/api/eventos/borrar", methods=["POST"])
def borrar_evento():
    eventos = cargar_datos()
    datos_a_borrar = request.json
    eventos = [e for e in eventos if e['title'] != datos_a_borrar['titulo']]
    guardar_datos(eventos)
    return jsonify({"mensaje": "Evento eliminado"})

@app.route("/crear-evento", methods=["GET", "POST"])
def crear_evento():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        fecha = request.form.get("fecha")
        tipo = request.form.get("tipo")

        if not nombre or not fecha or not tipo:
            return render_template("crear_evento.html", error="Por favor completa todos los campos 💖")

        eventos = cargar_datos()
        nuevo_evento = {
            "nombre": nombre,
            "fecha": fecha,
            "tipo": tipo
        }
        eventos.append(nuevo_evento)
        guardar_datos(eventos)
        return render_template("crear_evento.html", exito="Evento creado con éxito ✨")

    return render_template("crear_evento.html")


if __name__ == "__main__":
    app.run(debug=True)