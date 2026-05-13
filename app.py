from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import json
import os
import anthropic

app = Flask(__name__)
app.secret_key = 'lunefia_secret_key_2024'

ARCHIVO_DATOS = 'eventos.json'
USUARIOS_FILE = 'usuarios.json'
CLAVE_CLAUDE = "TU_API_KEY_AQUI"

def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def guardar_datos(datos):
    with open(ARCHIVO_DATOS, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=4)

def cargar_usuarios():
    if os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def guardar_usuarios(usuarios):
    with open(USUARIOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(usuarios, f, indent=4)

def obtener_mensaje_ia(eventos):
    try:
        client = anthropic.Anthropic(api_key=CLAVE_CLAUDE)
        contexto = ""
        if not eventos:
            contexto = "No hay eventos programados."
        else:
            for e in eventos:
                titulo = e.get('title', 'Sin título')
                fecha = e.get('start', 'Sin fecha')
                contexto += f"- {titulo} el {fecha}\n"

        prompt = f"""
        Eres 'Lunefia IA', asistente de un calendario grupal. 
        Tono: Amable, breve y con temática lunar/estelar.
        Eventos: {contexto}
        Tarea: Escribe un resumen de máximo 15 palabras para el usuario.
        """

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=60,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception:
        return "¡Todo tranquilo por ahora! No tienes eventos en los próximos días 🌙"

@app.before_request
def proteger_rutas():
    rutas_publicas = ['login', 'registro', 'static']
    if 'usuario' not in session and request.endpoint not in rutas_publicas:
        return redirect(url_for('login'))

@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/registro", methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        usuarios = cargar_usuarios()
        usuarios.append({"user": username, "pass": password})
        guardar_usuarios(usuarios)
        return redirect(url_for('login'))
    return render_template('registro.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        usuarios = cargar_usuarios()
        for u in usuarios:
            if u['user'] == username and u['pass'] == password:
                session['usuario'] = username
                return redirect(url_for('inicio'))
        return "Credenciales incorrectas", 401
    return render_template('login.html')

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/api/ia/resumen")
def resumen_ia():
    eventos = cargar_datos()
    mensaje = obtener_mensaje_ia(eventos)
    return jsonify({"mensaje": mensaje})

@app.route("/api/eventos", methods=["GET", "POST"])
def manejar_eventos():
    eventos = cargar_datos()
    if request.method == "POST":
        nuevo_evento = request.json
        eventos.append(nuevo_evento)
        guardar_datos(eventos)
        return jsonify({"mensaje": "Evento guardado"}), 201
    return jsonify(eventos)

@app.route("/api/eventos/borrar", methods=["POST"])
def borrar_evento():
    eventos = cargar_datos()
    datos_a_borrar = request.json
    eventos = [e for e in eventos if e.get('title') != datos_a_borrar.get('titulo')]
    guardar_datos(eventos)
    return jsonify({"mensaje": "Evento eliminado"})

@app.route('/api/notas', methods=['GET', 'POST'])
def gestionar_notas():
    if request.method == 'POST':
        return jsonify({"status": "nota guardada"})
    return jsonify({"notas": []})

if __name__ == "__main__":
    app.run(debug=True)