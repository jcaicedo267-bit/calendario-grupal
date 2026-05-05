from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def inicio():
    return render_template("index.html")

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
    