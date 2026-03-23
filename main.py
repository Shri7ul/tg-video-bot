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

# progress control
last_update = {}

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


# progress hook
def progress_hook(d, chat_id):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0%').replace('%', '').strip()

        try:
            percent = int(float(percent))
        except:
            percent = 0

        if chat_id not in last_update:
            last_update[chat_id] = 0

        if percent - last_update[chat_id] >= 10:
            last_update[chat_id] = percent
            send_message(chat_id, f"Downloading... {percent}%")


# download function
def download_video(url, chat_id, low_quality=False):
    ydl_opts = {
        'outtmpl': 'video.%(ext)s',
        'noplaylist': True,
        'progress_hooks': [lambda d: progress_hook(d, chat_id)],
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

            if "message" not in update:
                continue

            chat_id = update["message"]["chat"]["id"]
            text = update["message"].get("text", "")

            # start command
            if text.startswith("/start"):
                send_message(chat_id, "Link dao, ami video download kore dibo 📥")
                continue

            # validation
            if not text.startswith("http"):
                send_message(chat_id, "Valid link dao ❌")
                continue

            send_message(chat_id, "Processing link... 🔍")

            try:
                # high quality
                file_path = download_video(text, chat_id)
                size = os.path.getsize(file_path)

                # fallback low quality
                if size > 50 * 1024 * 1024:
                    os.remove(file_path)
                    send_message(chat_id, "File too large, trying low quality... ⚡")

                    file_path = download_video(text, chat_id, low_quality=True)
                    size = os.path.getsize(file_path)

                    if size > 50 * 1024 * 1024:
                        os.remove(file_path)
                        send_message(chat_id, "Still too large ❌")
                        continue

                send_message(chat_id, "Uploading... 📤")

                send_video(chat_id, file_path)
                os.remove(file_path)

                send_message(chat_id, "Done ✅")

            except Exception as e:
                send_message(chat_id, f"Error: {str(e)}")

        time.sleep(2)


if __name__ == "__main__":
    main()
