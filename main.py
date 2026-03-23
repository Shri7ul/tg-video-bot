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

def download_video(url):
    ydl_opts = {
        'outtmpl': 'video.%(ext)s',
        'format': 'mp4',
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

def main():
    print("Bot running...")

    # run web server in background
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
                else:
                    send_message(chat_id, "Downloading... ⏳")

                    try:
                        file_path = download_video(text)
                        send_video(chat_id, file_path)
                        os.remove(file_path)
                    except Exception as e:
                        send_message(chat_id, f"Error: {str(e)}")

        time.sleep(2)
if __name__ == "__main__":
    main()
