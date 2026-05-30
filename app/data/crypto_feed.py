import time as _time
import pandas as pd

from app.core.logger import logger

try:
    from binance.client import Client
    client = Client()
except Exception:
    client = None
    logger.warning("Binance client unavailable — crypto feeds disabled")


def get_crypto_data(symbol="BTCUSDT", interval="5m", limit=200):
    """
    Fetch crypto OHLCV data from Binance.

    Returns DataFrame with columns:
        time, open, high, low, close, volume
    """

    if client is None:
        logger.error(f"Binance client not initialized for {symbol}")
        return pd.DataFrame()

    for attempt in range(3):
        try:
            logger.info(f"Fetching crypto data: {symbol}")

            klines = client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit,
            )

            df = pd.DataFrame(klines)
            df = df.iloc[:, :6]

            df.columns = [
                "time",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ]

            numeric_cols = ["open", "high", "low", "close", "volume"]
            df[numeric_cols] = df[numeric_cols].astype(float)

            logger.info(f"Loaded {len(df)} candles for {symbol}")
            return df

        except Exception as e:
            logger.error(
                f"Attempt {attempt + 1}: "
                f"crypto fetch failed {symbol}: {e}"
            )
            _time.sleep(2)

    logger.error(f"Failed to fetch crypto data: {symbol}")
    return pd.DataFrame()