from binance.client import Client
import pandas as pd 

client = Client()


def get_crypto_data(symbol="BTCUSDT", interval=)


class BinanceFeed:
    def __init__(self, api_key, api_secret):
        self.client = Client(api_key, api_secret)
    
    def get_historical_data(self, symbol, interval, start_time, end_time):
        klines = self.client.get_historical_klines(symbol, interval, start_time, end_time)
        df = pd.DataFrame(klines, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df
    