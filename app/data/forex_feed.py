import yfinance as yf


FOREX_MAP = {
    "EURGBP": "EURGBP=X",
    "NZDCAD": "NZDCAD=X",
    "XAUUSD": "GC=F",
    "NAS100": "^NDX",
    "SP500": "^GSPC",
}


def get_forex_data(symbol, interval="5m"):
    ticker = FOREX_MAP[symbol]

    df = yf.download(ticker, interval=interval, period="7d", progress=False)

    return df