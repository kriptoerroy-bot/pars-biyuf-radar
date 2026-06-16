import requests
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def send_message(text, topic_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "message_thread_id": topic_id,
        "text": text,
        "disable_web_page_preview": True,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            print("✅ Mesaj gönderildi")
        else:
            print("❌ Hata:", response.text)

    except Exception as e:
        print("❌ Exception:", e)
