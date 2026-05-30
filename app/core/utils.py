from datetime import datetime
import pandas as pd
import numpy as np


def utc_now():
    return datetime.utcnow()


def current_hour():
    return utc_now().hour


def current_minute():
    return utc_now().minute


def current_second():
    return utc_now().second


def timestamp():
    return utc_now().strftime("%Y-%m-%d %H:%M:%S")


def validate_dataframe(df: pd.DataFrame, min_rows: int = 50):
    """Validate that a DataFrame has the required OHLCV columns and enough rows."""

    if df is None or df.empty:
        return False

    required_columns = ["time", "open", "high", "low", "close", "volume"]

    for column in required_columns:
        if column not in df.columns:
            return False

    if len(df) < min_rows:
        return False

    return True


def normalize_dataframe(df: pd.DataFrame):
    """Ensure numeric columns are float and sort by time."""

    numeric_columns = ["open", "high", "low", "close", "volume"]
    df[numeric_columns] = df[numeric_columns].astype(float)

    df = df.sort_values(by="time").reset_index(drop=True)
    return df


def candle_range(high, low):
    return high - low


def bullish_candle(open_price, close_price):
    return close_price > open_price


def bearish_candle(open_price, close_price):
    return close_price < open_price


def percentage_change(current_price, previous_price):
    if previous_price == 0:
        return 0.0
    return (current_price - previous_price) / previous_price * 100


def average_true_range(df: pd.DataFrame, period: int = 14):
    """Calculate Average True Range (ATR)."""

    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift(1)).abs()
    low_close = (df["low"] - df["close"].shift(1)).abs()

    true_range = pd.concat(
        [high_low, high_close, low_close], axis=1
    ).max(axis=1)

    atr = true_range.rolling(window=period).mean()
    return atr


def risk_reward_ratio(entry, stop_loss, take_profit):
    """Calculate risk:reward ratio."""

    risk = abs(entry - stop_loss)
    reward = abs(take_profit - entry)

    if risk == 0:
        return float("inf")

    return round(reward / risk, 2)


def recent_high(df: pd.DataFrame, lookback: int = 10):
    """Get the highest high over the last `lookback` candles."""
    return df["high"].iloc[-lookback:].max()


def recent_low(df: pd.DataFrame, lookback: int = 10):
    """Get the lowest low over the last `lookback` candles."""
    return df["low"].iloc[-lookback:].min()


def bullish_displacement(df: pd.DataFrame, multiplier: float = 1.5):
    """Check if the current candle is a bullish displacement (large bullish body)."""

    current_body = abs(df["close"].iloc[-1] - df["open"].iloc[-1])
    avg_body = abs(df["close"] - df["open"]).rolling(20).mean().iloc[-1]

    return (
        df["close"].iloc[-1] > df["open"].iloc[-1]
        and current_body > avg_body * multiplier
    )


def bearish_displacement(df: pd.DataFrame, multiplier: float = 1.5):
    """Check if the current candle is a bearish displacement (large bearish body)."""

    current_body = abs(df["close"].iloc[-1] - df["open"].iloc[-1])
    avg_body = abs(df["close"] - df["open"]).rolling(20).mean().iloc[-1]

    return (
        df["close"].iloc[-1] < df["open"].iloc[-1]
        and current_body > avg_body * multiplier
    )