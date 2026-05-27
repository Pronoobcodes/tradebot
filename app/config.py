from dotenv import load_dotenv
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")



TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

MAX_TRADES_PER_DAY = 3

SYMBOLS = {
    "BTCUSDT": {
        "type": "crypto",
        "session": "crypto_morning",
        "timeframe": "5m",
    },

    "ETHUSDT": {
        "type": "crypto",
        "session": "crypto_morning",
        "timeframe": "5m",
    },

    "EURGBP": {
        "type": "forex",
        "session": "london",
        "timeframe": "5m",
    },

    "NZDCAD": {
        "type": "forex",
        "session": "london",
        "timeframe": "5m",
    },

    "XAUUSD": {
        "type": "commodity",
        "session": "ny",
        "timeframe": "1m",
    },

    "NAS100": {
        "type": "index",
        "session": "ny",
        "timeframe": "1m",
    },

    "SP500": {
        "type": "index",
        "session": "ny",
        "timeframe": "1m",
    }
}