from flask import Flask, request, render_template, send_file, redirect, url_for
import os
import shutil
import subprocess
from text_to_speech import TextToSpeech, ConvertirVideo

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'input/'
app.config['OUTPUT_FOLDER'] = 'output/'
app.config['VIDEO_PATH'] = 'E:/PODCAST_2PY3.10.11/input/Spectrum.mp4'

def clean_output_folder():
    folder = app.config['OUTPUT_FOLDER']
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Limpiar el directorio de salida antes de procesar
        clean_output_folder()

        # Procesar el archivo
        tts = TextToSpeech(file_path)
        text = tts.read_text()
        if text:
            audio_file_path = tts.convert_to_speech(text)
            output_video_filename = 'output_video.mp4'
            output_video_path = os.path.join(app.config['OUTPUT_FOLDER'], output_video_filename)
            srt_file_path = os.path.join(app.config['OUTPUT_FOLDER'], 'output_video.srt')

            convertir_video = ConvertirVideo(audio_file_path, output_video_path, app.config['VIDEO_PATH'])
            convertir_video.attach_audio_to_video()

            tts.create_srt_word_by_word(audio_file_path, srt_file_path)

            # Abrir el archivo de video con VLC al finalizar
            subprocess.run(["vlc", output_video_path])

            return render_template('download.html')

    return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['OUTPUT_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    app.run(debug=True)
