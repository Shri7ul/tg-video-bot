import os
import time
import requests
import yt_dlp
from flask import Flask
import threading

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_web():
    app.run(host="0.0.0.0", port=10000)


BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    params = {"timeout": 30, "offset": offset}
    return requests.get(url, params=params).json()


def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text})


def send_video(chat_id, file_path):
    url = f"{BASE_URL}/sendVideo"
    with open(file_path, "rb") as f:
        requests.post(url, data={"chat_id": chat_id}, files={"video": f})


# 🔥 download with quality control
def download_video(url, low_quality=False):
    ydl_opts = {
        'outtmpl': 'video.%(ext)s',
        'noplaylist': True,
    }

    if low_quality:
        ydl_opts['format'] = 'worst[ext=mp4]'
    else:
        ydl_opts['format'] = 'best[ext=mp4]'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


def main():
    print("Bot running...")

    threading.Thread(target=run_web).start()

    offset = None

    while True:
        data = get_updates(offset)

        for update in data.get("result", []):
            offset = update["update_id"] + 1

            if "message" in update:
                chat_id = update["message"]["chat"]["id"]
                text = update["message"].get("text", "")

                if text.startswith("/start"):
                    send_message(chat_id, "Link dao, ami video download kore dibo 📥")
                    continue

                send_message(chat_id, "Downloading... ⏳")

                try:
                    # 🔥 first try high quality
                    file_path = download_video(text)

                    size = os.path.getsize(file_path)

                    # ✅ যদি 50MB এর বেশি হয়
                    if size > 50 * 1024 * 1024:
                        os.remove(file_path)

                        send_message(chat_id, "File too large, trying low quality... ⚡")

                        # 🔥 retry low quality
                        file_path = download_video(text, low_quality=True)
                        size = os.path.getsize(file_path)

                        if size > 50 * 1024 * 1024:
                            os.remove(file_path)
                            send_message(chat_id, "Still too large ❌\nUse smaller video or I’ll add link system later.")
                            continue

                    # ✅ send video
                    send_video(chat_id, file_path)
                    os.remove(file_path)

                except Exception as e:
                    send_message(chat_id, f"Error: {str(e)}")

        time.sleep(2)


if __name__ == "__main__":
    main()
