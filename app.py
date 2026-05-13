from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = 'lunefia_secret_key_2024'

ARCHIVO_DATOS = 'eventos.json'
USUARIOS_FILE = 'usuarios.json'
NOTAS_FILE = 'notas.json'
CALENDARIOS_FILE = 'calendarios.json'

def cargar_json(archivo):
    if os.path.exists(archivo):
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return [] if "notas" not in archivo else {"texto": ""}
    return [] if "notas" not in archivo else {"texto": ""}

def guardar_json(archivo, datos):
    with open(archivo, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=4)

@app.before_request
def proteger_rutas():
    rutas_publicas = ['login', 'registro', 'static']
    if 'usuario' not in session and request.endpoint not in rutas_publicas:
        return redirect(url_for('login'))

@app.route("/")
def inicio():
    # ACTUALIZADO: Ahora apunta a formato_calendario.html
    return render_template("formato_calendario.html")

@app.route("/registro", methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        user = request.form.get('correo')
        pw = request.form.get('contrasena')
        usuarios = cargar_json(USUARIOS_FILE)
        usuarios.append({"user": user, "pass": pw})
        guardar_json(USUARIOS_FILE, usuarios)
        return redirect(url_for('login'))
    return render_template('registro.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('correo')
        pw = request.form.get('contrasena')
        usuarios = cargar_json(USUARIOS_FILE)
        for u in usuarios:
            if u['user'] == user and u['pass'] == pw:
                session['usuario'] = user
                return redirect(url_for('inicio'))
        return "Error: Datos incorrectos", 401
    return render_template('login.html')

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/api/eventos", methods=["GET", "POST"])
def manejar_eventos():
    eventos = cargar_json(ARCHIVO_DATOS)
    if request.method == "POST":
        nuevo_evento = request.json
        eventos.append(nuevo_evento)
        guardar_json(ARCHIVO_DATOS, eventos)
        return jsonify({"mensaje": "Evento guardado"}), 201
    return jsonify(eventos)

@app.route("/api/eventos/borrar", methods=["POST"])
def borrar_evento():
    eventos = cargar_json(ARCHIVO_DATOS)
    datos_a_borrar = request.json
    titulo_objetivo = datos_a_borrar.get('titulo')
    eventos_filtrados = [e for e in eventos if e.get('title') != titulo_objetivo]
    guardar_json(ARCHIVO_DATOS, eventos_filtrados)
    return jsonify({"status": "eliminado"})

@app.route('/api/notas', methods=['GET', 'POST'])
def gestionar_notas():
    if request.method == 'POST':
        datos = request.json
        guardar_json(NOTAS_FILE, datos)
        return jsonify({"status": "nota guardada"})
    notas = cargar_json(NOTAS_FILE)
    return jsonify(notas if isinstance(notas, dict) else {"texto": ""})

@app.route('/api/calendarios', methods=['GET', 'POST'])
def gestionar_calendarios():
    lista = cargar_json(CALENDARIOS_FILE)
    if request.method == 'POST':
        nuevo = request.json
        lista.append(nuevo)
        guardar_json(CALENDARIOS_FILE, lista)
        return jsonify({"status": "ok"})
    return jsonify(lista)

if __name__ == "__main__":
    app.run(debug=True)