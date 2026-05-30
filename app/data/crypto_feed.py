from binance.client import Client
import pandas as pd 

client = Client()


def get_crypto_data(symbol="BTCUSDT", interval="5m", limit=200):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines)
    df = df.iloc[:, :6]
    df.columns = [
        "time",
        "open",
        "low",
        "close",
        "volume"
    ]

    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)

    return df


    
    