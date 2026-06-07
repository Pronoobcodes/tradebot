import time as _time
import pandas as pd
import yfinance as yf

from app.core.logger import logger

try:
    from binance.client import Client
    client = Client()
except Exception:
    client = None
    logger.warning("Binance client unavailable — using yfinance fallback for crypto")


CRYPTO_YF_MAP = {
    "BTCUSDT": "BTC-USD",
    "ETHUSDT": "ETH-USD",
}


def _normalize_yfinance_df(df):
    """
    Normalize a yfinance DataFrame to standard columns.

    Handles multi-index columns and various datetime column names
    that yfinance produces across different versions.

    Returns DataFrame with: time, open, high, low, close, volume
    """

    # Handle multi-index columns (yfinance >= 0.2.31)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.reset_index(inplace=True)

    # yfinance names the datetime column differently:
    # 'Datetime' for intraday, 'Date' for daily, or 'index' if unnamed
    datetime_col = None
    for candidate in ["Datetime", "Date", "index"]:
        if candidate in df.columns:
            datetime_col = candidate
            break

    if datetime_col is None:
        # Last resort: use first column
        datetime_col = df.columns[0]

    rename_map = {
        datetime_col: "time",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    }

    # Only rename columns that exist
    rename_map = {k: v for k, v in rename_map.items() if k in df.columns}
    df.rename(columns=rename_map, inplace=True)

    if "volume" not in df.columns:
        df["volume"] = 0

    # Drop Adj Close if present
    if "Adj Close" in df.columns:
        df.drop(columns=["Adj Close"], inplace=True)

    required = ["time", "open", "high", "low", "close", "volume"]
    df = df[required]

    numeric_cols = ["open", "high", "low", "close", "volume"]
    df[numeric_cols] = df[numeric_cols].astype(float)

    return df


def get_crypto_data(symbol="BTCUSDT", interval="5m", limit=200):
    """
    Fetch crypto OHLCV data from Binance (or yfinance fallback).

    Returns DataFrame with columns:
        time, open, high, low, close, volume
    """

    if client is not None:
        for attempt in range(3):
            try:
                logger.info(f"Fetching crypto data from Binance: {symbol}")

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

                logger.info(f"Loaded {len(df)} candles for {symbol} from Binance")
                return df

            except Exception as e:
                logger.error(
                    f"Attempt {attempt + 1}: "
                    f"Binance crypto fetch failed for {symbol}: {e}"
                )
                _time.sleep(2)

    # Fallback to yfinance
    yf_symbol = CRYPTO_YF_MAP.get(symbol)
    if not yf_symbol:
        logger.error(f"No yfinance fallback mapping found for crypto symbol {symbol}")
        return pd.DataFrame()

    for attempt in range(3):
        try:
            logger.info(f"Fetching crypto data from yfinance fallback: {symbol} ({yf_symbol})")
            
            # Map intervals to yfinance (Binance '5m' -> yfinance '5m')
            # 'limit' not directly supported by yfinance period, we'll fetch last 5 days
            df = yf.download(
                yf_symbol,
                period="5d",
                interval=interval,
                progress=False,
                auto_adjust=False,
            )

            if df.empty:
                logger.warning(f"Empty crypto data from yfinance: {symbol}")
                continue

            df = _normalize_yfinance_df(df)
            if limit and len(df) > limit:
                df = df.iloc[-limit:]

            logger.info(f"Loaded {len(df)} candles for {symbol} from yfinance fallback")
            return df
        except Exception as e:
            logger.error(
                f"Attempt {attempt + 1}: "
                f"yfinance crypto fallback fetch failed for {symbol}: {e}"
            )
            _time.sleep(2)

    logger.error(f"Failed to fetch crypto data: {symbol}")
    return pd.DataFrame()