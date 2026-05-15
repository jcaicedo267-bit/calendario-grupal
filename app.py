from flask import Flask, render_template, request, jsonify, redirect, session
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = "lunefia_secretkey_2026"

DATABASE_URL = "postgresql://admin_lunefia:mhj46c94U8UPA6OeOZbb6TclASkZn0Pz@dpg-d83750lckfvc73bb451g-a.ohio-postgres.render.com/lunefia_db"

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            nombre TEXT PRIMARY KEY,
            contrasena TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS calendarios (
            id SERIAL PRIMARY KEY,
            nombre TEXT,
            tipo TEXT,
            dueno TEXT,
            integrantes TEXT
        );
        CREATE TABLE IF NOT EXISTS eventos (
            id SERIAL PRIMARY KEY,
            title TEXT,
            start TEXT,
            end_time TEXT,
            calendario INTEGER,
            dueno TEXT,
            materia TEXT,
            modalidad TEXT,
            partes TEXT
        );
        CREATE TABLE IF NOT EXISTS notas (
            id SERIAL PRIMARY KEY,
            usuario TEXT,
            calendario INTEGER,
            texto TEXT,
            UNIQUE(usuario, calendario)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# Llama init_db al arrancar
with app.app_context():
    init_db()

# -------- HELPERS --------
def usuario_actual():
    return session.get("usuario")

def login_requerido():
    if not usuario_actual():
        return redirect("/login")
    return None

# -------- PÁGINAS --------
@app.route("/")
def inicio():
    redir = login_requerido()
    if redir: return redir
    return render_template("home.html", usuario=session.get("usuario"))

@app.route("/calendario/<int:cal_id>")
def ver_calendario(cal_id):
    redir = login_requerido()
    if redir: return redir
    return render_template("calendario.html", usuario=session.get("usuario"))

# -------- AUTH --------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario    = request.form.get("usuario")
        contrasena = request.form.get("contraseña")
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT * FROM usuarios WHERE nombre = %s AND contrasena = %s", (usuario, contrasena))
        user = cur.fetchone()
        cur.close(); conn.close()
        if user:
            session["usuario"] = usuario
            return redirect("/")
        return render_template("login.html", error="Usuario o contraseña incorrectos 💔")
    return render_template("login.html")

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        usuario    = request.form.get("usuario")
        contrasena = request.form.get("contraseña")
        if not usuario or not contrasena:
            return render_template("registro.html", error="Completa todos los campos 💔")
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("INSERT INTO usuarios (nombre, contrasena) VALUES (%s, %s)", (usuario, contrasena))
            conn.commit()
            session["usuario"] = usuario
            cur.close(); conn.close()
            return redirect("/")
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            cur.close(); conn.close()
            return render_template("registro.html", error="Ese usuario ya existe 💔")
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
    conn = get_db(); cur = conn.cursor()

    if request.method == "POST":
        datos = request.get_json()
        cur.execute(
            "INSERT INTO calendarios (nombre, tipo, dueno, integrantes) VALUES (%s, %s, %s, %s) RETURNING id",
            (datos.get("nombre"), datos.get("tipo"), usuario, datos.get("integrantes", ""))
        )
        new_id = cur.fetchone()["id"]
        conn.commit(); cur.close(); conn.close()
        return jsonify({"mensaje": "Calendario guardado 💖", "id": new_id})

    cur.execute(
        "SELECT * FROM calendarios WHERE tipo = 'grupal' OR dueno = %s", (usuario,)
    )
    calendarios = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([dict(c) for c in calendarios])

@app.route("/api/calendarios/<int:cal_id>", methods=["DELETE"])
def borrar_calendario(cal_id):
    redir = login_requerido()
    if redir: return jsonify({"error": "no autenticado"}), 401
    usuario = usuario_actual()
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM calendarios WHERE id = %s", (cal_id,))
    cal = cur.fetchone()
    if not cal:
        cur.close(); conn.close()
        return jsonify({"error": "no encontrado"}), 404
    if cal["dueno"] != usuario:
        cur.close(); conn.close()
        return jsonify({"error": "sin permiso"}), 403
    cur.execute("DELETE FROM calendarios WHERE id = %s", (cal_id,))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"mensaje": "Calendario eliminado"})

# -------- EVENTOS --------
@app.route("/api/eventos", methods=["GET", "POST"])
def manejar_eventos():
    redir = login_requerido()
    if redir: return jsonify({"error": "no autenticado"}), 401
    usuario = usuario_actual()
    conn = get_db(); cur = conn.cursor()

    if request.method == "POST":
        e = request.get_json()
        cur.execute(
            "INSERT INTO eventos (title, start, \"end\", calendario, dueno, materia, modalidad, partes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (e.get("title"), e.get("start"), e.get("end"), e.get("calendario"), usuario,
             e.get("materia"), e.get("modalidad"), e.get("partes"))
        )
        conn.commit(); cur.close(); conn.close()
        return jsonify({"mensaje": "Evento guardado correctamente"}), 201

    cal_id = request.args.get("calendario")
    if cal_id:
        cur.execute("SELECT * FROM calendarios WHERE id = %s", (cal_id,))
        cal = cur.fetchone()
        if cal:
            if cal["tipo"] == "grupal":
                cur.execute("SELECT * FROM eventos WHERE calendario = %s", (cal_id,))
            else:
                cur.execute("SELECT * FROM eventos WHERE calendario = %s AND dueno = %s", (cal_id, usuario))
            resultado = cur.fetchall()
        else:
            resultado = []
    else:
        cur.execute("SELECT id FROM calendarios WHERE tipo = 'grupal'")
        grupales = [str(r["id"]) for r in cur.fetchall()]
        if grupales:
            cur.execute(
                f"SELECT * FROM eventos WHERE dueno = %s OR calendario::text = ANY(%s)",
                (usuario, grupales)
            )
        else:
            cur.execute("SELECT * FROM eventos WHERE dueno = %s", (usuario,))
        resultado = cur.fetchall()

    cur.close(); conn.close()
    return jsonify([dict(e) for e in resultado])

@app.route("/api/eventos/borrar", methods=["POST"])
def borrar_evento():
    redir = login_requerido()
    if redir: return jsonify({"error": "no autenticado"}), 401
    usuario = usuario_actual()
    datos = request.get_json()
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM eventos WHERE title = %s AND dueno = %s", (datos.get("titulo"), usuario))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"mensaje": "Evento eliminado"})

# -------- NOTAS --------
@app.route("/api/notas", methods=["GET", "POST"])
def manejar_notas():
    redir = login_requerido()
    if redir: return jsonify({"error": "no autenticado"}), 401
    usuario = usuario_actual()
    conn = get_db(); cur = conn.cursor()

    if request.method == "POST":
        datos = request.get_json()
        cur.execute(
            """INSERT INTO notas (usuario, calendario, texto) VALUES (%s, %s, %s)
               ON CONFLICT (usuario, calendario) DO UPDATE SET texto = EXCLUDED.texto""",
            (usuario, datos.get("calendario"), datos.get("texto"))
        )
        conn.commit(); cur.close(); conn.close()
        return jsonify({"mensaje": "Nota guardada ✨"})

    cal_id = request.args.get("calendario")
    cur.execute("SELECT texto FROM notas WHERE usuario = %s AND calendario = %s", (usuario, cal_id))
    nota = cur.fetchone()
    cur.close(); conn.close()
    return jsonify({"texto": nota["texto"] if nota else ""})

# -------- PERFIL --------
@app.route("/api/perfil", methods=["POST"])
def actualizar_perfil():
    redir = login_requerido()
    if redir: return jsonify({"error": "no autenticado"}), 401
    usuario_viejo = usuario_actual()
    datos = request.get_json()
    nuevo_nombre = datos.get("nuevo_nombre", "").strip()
    nueva_pass   = datos.get("nueva_pass", "").strip()
    conn = get_db(); cur = conn.cursor()

    if nuevo_nombre and nuevo_nombre != usuario_viejo:
        cur.execute("SELECT nombre FROM usuarios WHERE nombre = %s", (nuevo_nombre,))
        if cur.fetchone():
            cur.close(); conn.close()
            return jsonify({"ok": False, "error": "Ese nombre ya existe 💔"})
        cur.execute("UPDATE usuarios SET nombre = %s WHERE nombre = %s", (nuevo_nombre, usuario_viejo))
        session["usuario"] = nuevo_nombre
        usuario_viejo = nuevo_nombre

    if nueva_pass:
        cur.execute("UPDATE usuarios SET contrasena = %s WHERE nombre = %s", (nueva_pass, usuario_viejo))

    conn.commit(); cur.close(); conn.close()
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(debug=True)