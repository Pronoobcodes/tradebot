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
        "sessions": ["asia", "london", "new_york"],
        "timeframe": "5m",
        "htf_timeframe": "1h",
    },

    "ETHUSDT": {
        "type": "crypto",
        "sessions": ["asia", "london", "new_york"],
        "timeframe": "5m",
        "htf_timeframe": "1h",
    },

    "EURGBP": {
        "type": "forex",
        "sessions": ["london"],
        "timeframe": "5m",
        "htf_timeframe": "4h",
    },

    "NZDCAD": {
        "type": "forex",
        "sessions": ["asia", "london"],
        "timeframe": "5m",
        "htf_timeframe": "4h",
    },

    "XAUUSD": {
        "type": "commodity",
        "sessions": ["london", "new_york"],
        "timeframe": "5m",
        "htf_timeframe": "4h",
    },

    "NAS100": {
        "type": "index",
        "sessions": ["ny_am"],
        "timeframe": "5m",
        "htf_timeframe": "1h",
    },

    "SP500": {
        "type": "index",
        "sessions": ["ny_am"],
        "timeframe": "5m",
        "htf_timeframe": "1h",
    }
}