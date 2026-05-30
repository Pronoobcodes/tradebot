import requests

from app.config import TELEGRAM_TOKEN, CHAT_ID
from app.core.logger import logger


def send_message(message, parse_mode="HTML"):
    """
    Send a message via Telegram Bot API.

    Uses HTML parse mode by default for formatted messages.
    Silently logs errors instead of crashing.
    """

    if not TELEGRAM_TOKEN or not CHAT_ID:
        logger.warning(
            "Telegram credentials not set — skipping notification"
        )
        return False

    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": parse_mode,
    }

    try:
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            logger.info("Telegram message sent")
            return True
        else:
            logger.error(
                f"Telegram send failed: "
                f"{response.status_code} — {response.text}"
            )
            return False

    except Exception as e:
        logger.error(f"Telegram error: {e}")
        return False