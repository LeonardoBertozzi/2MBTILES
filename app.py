import os
import subprocess
from flask import Flask, request, render_template, send_file

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def convert_pdf_to_mbtiles(input_pdf, output_mbtiles):
    output_tif = os.path.join(OUTPUT_FOLDER, "temp.tif")

    if os.path.exists(output_tif):
        os.remove(output_tif)

    # Converte PDF para GeoTIFF
    subprocess.run([
        'gdal_translate', '-of', 'GTiff', '-outsize', '200%', '200%',
        '-co', 'COMPRESS=LZW', '-co', 'TILED=YES', '-co', 'BIGTIFF=YES', '-co', 'PREDICTOR=2',
        input_pdf, output_tif
    ], check=True)

    # Converte GeoTIFF para MBTiles
    subprocess.run([
        'gdal_translate', '-of', 'MBTILES', '-co', 'QUALITY=100', '-co', 'ZLEVEL=9',
        output_tif, output_mbtiles
    ], check=True)

    os.remove(output_tif)  # Remove arquivo temporário

def convert_shp_to_mbtiles(input_shp, output_mbtiles):
    if os.path.exists(output_mbtiles):
        os.remove(output_mbtiles)

    subprocess.run([
        'ogr2ogr', '-f', 'MBTILES', output_mbtiles, input_shp,
        '-dsco', 'FORMAT=VECTOR', '-t_srs', 'EPSG:3857'
    ], check=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            filename = file.filename
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            ext = os.path.splitext(filename)[-1].lower()
            output_mbtiles = os.path.join(OUTPUT_FOLDER, filename.replace(ext, ".mbtiles"))

            try:
                if ext == ".pdf":
                    convert_pdf_to_mbtiles(filepath, output_mbtiles)
                elif ext == ".shp":
                    convert_shp_to_mbtiles(filepath, output_mbtiles)
                else:
                    return "Formato não suportado. Use PDF ou Shapefile.", 400

                return send_file(output_mbtiles, as_attachment=True)
            except Exception as e:
                return f"Erro na conversão: {e}", 500

    return render_template("index.html")

if __name__ == "__main__":
    from os import environ
    port = int(environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
