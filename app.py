from flask import Flask, request, render_template, send_file, redirect, url_for
import yt_dlp
import uuid
import os
import re

app = Flask(__name__)

class MyLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): print(f"[ERROR]: {msg}")

def extract_video_id(url):
    # Nếu url không bắt đầu bằng http, thêm https://
    if not url.startswith("http"):
        url = "https://" + url

    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",  # dạng: v=ID hoặc /ID
        r"youtu\.be\/([0-9A-Za-z_-]{11})"   # dạng youtu.be/ID
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    video_id = None
    filename = None

    if request.method == "POST":
        url = request.form.get("url")
        video_id = extract_video_id(url)

        try:
            # Tạo tên file tạm
            filename = f"{uuid.uuid4()}.mp4"

            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'outtmpl': filename,
                'logger': MyLogger(),
                'quiet': True,
                'noplaylist': True,
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4'
                }]
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Sau khi tải xong, truyền filename và video_id về để hiển thị nút tải và preview
            return render_template("index.html", error=error, video_id=video_id, filename=filename)

        except Exception as e:
            error = str(e)

    # GET hoặc lỗi thì chỉ hiển thị form bình thường
    return render_template("index.html", error=error, video_id=video_id, filename=filename)

@app.route("/download/<filename>")
def download(filename):
    # Kiểm tra file có tồn tại không trước khi gửi
    if os.path.exists(filename):
        # Gửi file và sau đó xóa file tạm
        response = send_file(filename, as_attachment=True)
        # Xóa file sau khi gửi
        @response.call_on_close
        def remove_file():
            if os.path.exists(filename):
                os.remove(filename)
        return response
    else:
        return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
