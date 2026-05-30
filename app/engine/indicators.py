import ta
import pandas as pd


def add_indicators(df: pd.DataFrame):
    """Add RSI and EMA-50 indicators to the dataframe."""

    df["rsi"] = ta.momentum.RSIIndicator(
        close=df["close"]
    ).rsi()

    df["ema_50"] = ta.trend.EMAIndicator(
        close=df["close"],
        window=50,
    ).ema_indicator()

    return df