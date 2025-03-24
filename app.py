from flask import Flask, render_template, request, redirect, url_for, send_file
import os
import subprocess

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# Configurar PATH para GDAL
os.environ['PATH'] += r';C:\OSGeo4W\bin'

def pdf_to_mbtiles(input_pdf, output_mbtiles):
    output_tif = os.path.join(RESULT_FOLDER, 'output.tif')
    
    # Converter PDF para TIFF com resolução adequada
    cmd_tif = ['gdal_translate', '-of', 'GTiff', '-outsize', '1280', '800', input_pdf, output_tif]
    subprocess.run(cmd_tif, check=True)
    
    # Adicionar sistema de referência espacial (SRS) se não estiver presente
    cmd_srs = ['gdalwarp', '-s_srs', 'EPSG:4326', '-t_srs', 'EPSG:4326', output_tif, output_tif]
    subprocess.run(cmd_srs, check=True)
    
    # Converter para MBTILES com nível de zoom configurado
    cmd_mbtiles = [
        'gdal_translate', 
        '-of', 'MBTILES',
        '-co', 'ZOOM_LEVEL=0-30',
        output_tif, output_mbtiles
    ]
    subprocess.run(cmd_mbtiles, check=True)
    
    os.remove(output_tif)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        # Ajustar o nome do arquivo de saída
        filename_without_extension = os.path.splitext(file.filename)[0]
        output_mbtiles = os.path.join(RESULT_FOLDER, f"microplan {filename_without_extension}.mbtiles")

        pdf_to_mbtiles(filepath, output_mbtiles)
        
        return redirect(url_for('download_file', filename=os.path.basename(output_mbtiles)))
    
    return render_template('upload.html')

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(RESULT_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    from os import environ
    port = int(environ.get("PORT", 555))
    app.run(host="0.0.0.0", port=port)
