from flask import Flask, render_template, request, jsonify, redirect, session
import json
import os

app = Flask(__name__)
app.secret_key = "lunefia_secretkey_2026"  # clave para las sesiones

# -------- ARCHIVOS --------
ARCHIVO_EVENTOS     = 'eventos.json'
ARCHIVO_USUARIOS    = 'usuarios.json'
ARCHIVO_NOTAS       = 'notas.json'
ARCHIVO_CALENDARIOS = 'calendarios.json'

# -------- HELPERS --------
def cargar_json(archivo, default):
    if os.path.exists(archivo):
        with open(archivo, 'r') as f:
            return json.load(f)
    return default

def guardar_json(archivo, datos):
    with open(archivo, 'w') as f:
        json.dump(datos, f, indent=4)

def usuario_actual():
    return session.get("usuario")

def login_requerido():
    """Devuelve redirect si no hay sesión, None si sí hay."""
    if not usuario_actual():
        return redirect("/login")
    return None

# -------- PÁGINAS --------
@app.route("/")
def inicio():
    redir = login_requerido()
    if redir: return redir
    return render_template("home.html")

@app.route("/calendario/<int:cal_id>")
def ver_calendario(cal_id):
    redir = login_requerido()
    if redir: return redir
    return render_template("calendario.html")

# -------- AUTH --------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario    = request.form.get("usuario")
        contraseña = request.form.get("contraseña")
        usuarios   = cargar_json(ARCHIVO_USUARIOS, {})
        if usuario in usuarios and usuarios[usuario] == contraseña:
            session["usuario"] = usuario
            return redirect("/")
        return render_template("login.html", error="Usuario o contraseña incorrectos 💔")
    return render_template("login.html")

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        usuario    = request.form.get("usuario")
        contraseña = request.form.get("contraseña")
        if not usuario or not contraseña:
            return render_template("registro.html", error="Completa todos los campos 💔")
        usuarios = cargar_json(ARCHIVO_USUARIOS, {})
        if usuario in usuarios:
            return render_template("registro.html", error="Ese usuario ya existe 💔")
        usuarios[usuario] = contraseña
        guardar_json(ARCHIVO_USUARIOS, usuarios)
        session["usuario"] = usuario
        return redirect("/")
    return render_template("registro.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# -------- CALENDARIOS --------
@app.route("/api/calendarios", methods=["GET", "POST"])
def manejar_calendarios():
    redir = login_requerido()
    if redir: return jsonify({"error": "no autenticado"}), 401

    usuario = usuario_actual()
    calendarios = cargar_json(ARCHIVO_CALENDARIOS, [])

    if request.method == "POST":
        datos = request.get_json()
        # Asignar ID único y dueño
        datos["id"]    = max([c.get("id", 0) for c in calendarios], default=0) + 1
        datos["dueño"] = usuario
        calendarios.append(datos)
        guardar_json(ARCHIVO_CALENDARIOS, calendarios)
        return jsonify({"mensaje": "Calendario guardado 💖", "id": datos["id"]})

    # GET: devolver grupales + los personales del usuario
    visibles = [
        c for c in calendarios
        if c.get("tipo") == "grupal" or c.get("dueño") == usuario
    ]
    return jsonify(visibles)

@app.route("/api/calendarios/<int:cal_id>", methods=["DELETE"])
def borrar_calendario(cal_id):
    redir = login_requerido()
    if redir: return jsonify({"error": "no autenticado"}), 401

    usuario = usuario_actual()
    calendarios = cargar_json(ARCHIVO_CALENDARIOS, [])
    cal = next((c for c in calendarios if c.get("id") == cal_id), None)

    if not cal:
        return jsonify({"error": "no encontrado"}), 404
    # Solo el dueño puede borrar
    if cal.get("dueño") != usuario:
        return jsonify({"error": "sin permiso"}), 403

    calendarios = [c for c in calendarios if c.get("id") != cal_id]
    guardar_json(ARCHIVO_CALENDARIOS, calendarios)
    return jsonify({"mensaje": "Calendario eliminado"})

# -------- EVENTOS --------
@app.route("/api/eventos", methods=["GET", "POST"])
def manejar_eventos():
    redir = login_requerido()
    if redir: return jsonify({"error": "no autenticado"}), 401

    usuario = usuario_actual()
    eventos = cargar_json(ARCHIVO_EVENTOS, [])

    if request.method == "POST":
        nuevo = request.get_json()
        nuevo["dueño"] = usuario
        eventos.append(nuevo)
        guardar_json(ARCHIVO_EVENTOS, eventos)
        return jsonify({"mensaje": "Evento guardado correctamente"}), 201

    # GET: filtrar por calendario si se pasa el parámetro
    cal_id = request.args.get("calendario")
    calendarios = cargar_json(ARCHIVO_CALENDARIOS, [])

    if cal_id:
        cal = next((c for c in calendarios if str(c.get("id")) == str(cal_id)), None)
        if cal:
            if cal.get("tipo") == "grupal":
                # Calendario grupal: todos ven todos los eventos
                resultado = [e for e in eventos if str(e.get("calendario")) == str(cal_id)]
            else:
                # Calendario personal: solo los del dueño
                resultado = [
                    e for e in eventos
                    if str(e.get("calendario")) == str(cal_id) and e.get("dueño") == usuario
                ]
        else:
            resultado = []
    else:
        # Sin filtro: eventos del usuario + eventos de calendarios grupales
        grupales = {str(c["id"]) for c in calendarios if c.get("tipo") == "grupal"}
        resultado = [
            e for e in eventos
            if e.get("dueño") == usuario or str(e.get("calendario")) in grupales
        ]

    return jsonify(resultado)

@app.route("/api/eventos/borrar", methods=["POST"])
def borrar_evento():
    redir = login_requerido()
    if redir: return jsonify({"error": "no autenticado"}), 401

    usuario = usuario_actual()
    eventos = cargar_json(ARCHIVO_EVENTOS, [])
    datos   = request.get_json()

    # Solo borrar eventos propios (o en calendario grupal si eres el dueño del evento)
    eventos = [
        e for e in eventos
        if not (e.get("title") == datos.get("titulo") and e.get("dueño") == usuario)
    ]
    guardar_json(ARCHIVO_EVENTOS, eventos)
    return jsonify({"mensaje": "Evento eliminado"})

# -------- NOTAS --------
@app.route("/api/notas", methods=["GET", "POST"])
def manejar_notas():
    redir = login_requerido()
    if redir: return jsonify({"error": "no autenticado"}), 401

    usuario = usuario_actual()
    notas   = cargar_json(ARCHIVO_NOTAS, [])
    cal_id  = request.args.get("calendario") or (request.get_json() or {}).get("calendario")

    if request.method == "POST":
        datos = request.get_json()
        # Reemplazar nota existente del mismo usuario y calendario
        notas = [
            n for n in notas
            if not (n.get("usuario") == usuario and str(n.get("calendario")) == str(datos.get("calendario")))
        ]
        notas.append({"usuario": usuario, "calendario": datos.get("calendario"), "texto": datos.get("texto")})
        guardar_json(ARCHIVO_NOTAS, notas)
        return jsonify({"mensaje": "Nota guardada ✨"})

    # GET: buscar nota del usuario para ese calendario
    nota = next(
        (n for n in notas if n.get("usuario") == usuario and str(n.get("calendario")) == str(cal_id)),
        None
    )
    return jsonify({"texto": nota["texto"] if nota else ""})

if __name__ == "__main__":
    app.run(debug=True)