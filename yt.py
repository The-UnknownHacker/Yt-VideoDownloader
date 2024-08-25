from flask import Flask, request, send_file, jsonify, render_template, make_response, redirect, url_for
import yt_dlp
import os
import mimetypes
from io import BytesIO

app = Flask(__name__)

def get_video_info(url):
    """Fetch video information including available formats and resolutions."""
    with yt_dlp.YoutubeDL() as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])
        resolutions = sorted(set(fmt.get('height') for fmt in formats if fmt.get('height')), reverse=True)
        format_options = sorted(set(fmt.get('ext') for fmt in formats if fmt.get('ext')))
        return resolutions, format_options


def download_video(url, format_choice, resolution_choice):
    """Download video based on user choices."""
    ydl_opts = {}
    
    if format_choice == 'mp4':
        ydl_opts = {
            'format': f'bestvideo[height<={resolution_choice}]+bestaudio/best',
            'merge_output_format': 'mp4',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
        }
    elif format_choice == 'mp3':
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'downloads/%(title)s.%(ext)s',
        }
    elif format_choice == 'webm':
        ydl_opts = {
            'format': f'bestvideo[height<={resolution_choice}]+bestaudio/best',
            'merge_output_format': 'webm',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
        }
    elif format_choice == 'avi':
        ydl_opts = {
            'format': f'bestvideo[height<={resolution_choice}]+bestaudio/best',
            'merge_output_format': 'avi',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
        }
    else:
        return "Unsupported format selected."
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        download_dir = 'downloads'
        files = os.listdir(download_dir)
        video_files = [file for file in files if file.endswith(('.mp4', '.webm', '.avi', '.mp3'))]
        if video_files:
            filename = max(video_files, key=lambda x: os.path.getmtime(os.path.join(download_dir, x)))
            return os.path.join(download_dir, filename)
        else:
            return None


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        format_choice = request.form.get('format')
        resolution_choice = request.form.get('resolution')
        
        if url and format_choice and resolution_choice:
            try:
                filename = download_video(url, format_choice, resolution_choice)
                mime_type, _ = mimetypes.guess_type(filename)
                response = send_file(filename, as_attachment=True, mimetype=mime_type)
                return response
            except Exception as e:
                return f"An error occurred: {e}"
        else:
            return "Missing required fields."
        
        # This will not work because it's after the return statement
        # return redirect(url_for('success'))
    
    # So we put it here
    return redirect(url_for('success')) if request.method == 'POST' else render_template('index.html')

@app.route('/get_info', methods=['POST'])
def get_info():
    url = request.form.get('url')
    if url:
        resolutions, formats = get_video_info(url)
        return jsonify({'resolutions': resolutions, 'formats': formats})
    return jsonify({'error': 'Invalid URL'}), 400


@app.route('/success')
def success():
    return render_template('success.html')

if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    app.run(port=5001, debug=True)