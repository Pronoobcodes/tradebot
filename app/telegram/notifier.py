import requests

from app.config import TELEGRAM_TOKEN
from app.config import CHAT_ID



def send_message(message):

    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
    }

    requests.post(url, json=payload)