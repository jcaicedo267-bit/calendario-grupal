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
    return render_template("home.html")

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
# -------- USUARIOS --------
ARCHIVO_USUARIOS = 'usuarios.json'

def cargar_usuarios():
    if os.path.exists(ARCHIVO_USUARIOS):
        with open(ARCHIVO_USUARIOS, 'r') as f:
            return json.load(f)
    return {}

def guardar_usuarios(usuarios):
    with open(ARCHIVO_USUARIOS, 'w') as f:
        json.dump(usuarios, f, indent=4)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        contraseña = request.form.get("contraseña")
        usuarios = cargar_usuarios()
        if usuario in usuarios and usuarios[usuario] == contraseña:
            return render_template("home.html", usuario=usuario)
        return render_template("login.html", error="Usuario o contraseña incorrectos 💔")
    return render_template("login.html")

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        contraseña = request.form.get("contraseña")
        if not usuario or not contraseña:
            return render_template("registro.html", error="Completa todos los campos 💔")
        usuarios = cargar_usuarios()
        usuarios[usuario] = contraseña
        guardar_usuarios(usuarios)
        return render_template("home.html", usuario=usuario)
    return render_template("registro.html")

@app.route("/logout")
def logout():
    return render_template("login.html")

# -------- NOTAS --------
ARCHIVO_NOTAS = 'notas.json'

def cargar_notas():
    if os.path.exists(ARCHIVO_NOTAS):
        with open(ARCHIVO_NOTAS, 'r') as f:
            return json.load(f)
    return []

@app.route("/api/notas", methods=["GET", "POST"])
def manejar_notas():
    if request.method == "POST":
        datos = request.get_json()
        notas = cargar_notas()
        notas.append(datos)
        with open(ARCHIVO_NOTAS, 'w') as f:
            json.dump(notas, f, indent=4)
        return jsonify({"mensaje": "Nota guardada ✨"})
    return jsonify(cargar_notas())

# -------- CALENDARIOS --------
ARCHIVO_CALENDARIOS = 'calendarios.json'

def cargar_calendarios():
    if os.path.exists(ARCHIVO_CALENDARIOS):
        with open(ARCHIVO_CALENDARIOS, 'r') as f:
            return json.load(f)
    return []

@app.route("/api/calendarios", methods=["GET", "POST"])
def manejar_calendarios():
    if request.method == "POST":
        datos = request.get_json()
        calendarios = cargar_calendarios()
        calendarios.append(datos)
        with open(ARCHIVO_CALENDARIOS, 'w') as f:
            json.dump(calendarios, f, indent=4)
        return jsonify({"mensaje": "Calendario guardado 💖"})
    return jsonify(cargar_calendarios())

if __name__ == "__main__":
    app.run(debug=True)