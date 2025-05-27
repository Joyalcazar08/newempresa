from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
)
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import base64
import fitz  # PyMuPDF
from PIL import Image
import os
import mysql.connector

app = Flask(__name__)

# Configuraciones
UPLOAD_FOLDER = "static/uploads"
SIGNED_FOLDER = "static/firmados"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SIGNED_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SIGNED_FOLDER"] = SIGNED_FOLDER

# Documento base
DOCUMENTO_BASE = "static/documento_base.pdf"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/firmar", methods=["POST"])
def firmar():
    nombre = request.form["nombre"]
    identificador = request.form["identificador"]
    firma_data = request.form["firma"]  # base64
    foto1_data = request.form["foto1"]  # base64
    foto2_data = request.form["foto2"]  # base64

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    nombre_archivo = f"{secure_filename(nombre)}_{timestamp}"

    # Guardar firma
    firma_path = os.path.join(
        app.config["UPLOAD_FOLDER"], f"{nombre_archivo}_firma.png"
    )
    with open(firma_path, "wb") as f:
        f.write(base64.b64decode(firma_data.split(",")[1]))

    # Guardar foto 1
    foto1_path = os.path.join(
        app.config["UPLOAD_FOLDER"], f"{nombre_archivo}_foto1.jpg"
    )
    with open(foto1_path, "wb") as f:
        f.write(base64.b64decode(foto1_data.split(",")[1]))

    # Guardar foto 2
    foto2_path = os.path.join(
        app.config["UPLOAD_FOLDER"], f"{nombre_archivo}_foto2.jpg"
    )
    with open(foto2_path, "wb") as f:
        f.write(base64.b64decode(foto2_data.split(",")[1]))

    # Insertar en PDF
    pdf_ruta = os.path.join(
        app.config["SIGNED_FOLDER"], f"{nombre_archivo}_firmado.pdf"
    )
    insertar_en_pdf(DOCUMENTO_BASE, firma_path, foto1_path, foto2_path, pdf_ruta)

    return redirect(url_for("descargar", filename=os.path.basename(pdf_ruta)))


@app.route("/descargar/<filename>")
def descargar(filename):
    return send_from_directory(app.config["SIGNED_FOLDER"], filename)


def insertar_en_pdf(pdf_path, firma_img, foto1_img, foto2_img, output_path):
    doc = fitz.open(pdf_path)
    page = doc[0]

    # Redimensionar imágenes
    firma = Image.open(firma_img)
    firma.thumbnail((150, 80))
    firma.save(firma_img)

    foto1 = Image.open(foto1_img)
    foto1.thumbnail((100, 100))
    foto1.save(foto1_img)

    foto2 = Image.open(foto2_img)
    foto2.thumbnail((100, 100))
    foto2.save(foto2_img)

    width = page.rect.width
    height = page.rect.height

    # Ubicación firma (50px desde izquierda, 150px desde abajo)
    y_firma_top = height - 400
    y_firma_bottom = y_firma_top + 80
    firma_rect = fitz.Rect(50, y_firma_top, 50 + 150, y_firma_bottom)
    page.insert_image(firma_rect, filename=firma_img)

    # Fotos debajo de la firma, lado a lado con separación 10px

    # Foto 1 (izquierda)
    foto1_x1 = 50
    foto1_y1 = y_firma_bottom + 10
    foto1_x2 = foto1_x1 + 100
    foto1_y2 = foto1_y1 + 100
    foto1_rect = fitz.Rect(foto1_x1, foto1_y1, foto1_x2, foto1_y2)
    page.insert_image(foto1_rect, filename=foto1_img)

    # Foto 2 (derecha)
    foto2_x1 = foto1_x2 + 10
    foto2_y1 = foto1_y1
    foto2_x2 = foto2_x1 + 100
    foto2_y2 = foto1_y2
    foto2_rect = fitz.Rect(foto2_x1, foto2_y1, foto2_x2, foto2_y2)
    page.insert_image(foto2_rect, filename=foto2_img)

    doc.save(output_path)
    doc.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
