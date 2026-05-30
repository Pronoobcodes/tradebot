from app.config import SYMBOLS
from app.data.crypto_feed import get_crypto_data
from app.data.forex_feed import get_forex_data


def get_market_data(symbol):
    asset = SYMBOLS[symbol]

    if asset["type"] == "crypto":
        return get_crypto_data(symbol)

    if asset["type"] == "forex":
        return get_forex_data(symbol)

    return None
    