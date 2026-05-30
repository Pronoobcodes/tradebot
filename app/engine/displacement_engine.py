import pandas as pd


def candle_body(open_price, close_price):
    return abs(close_price - open_price)


def average_body(df: pd.DataFrame, period=20):
    bodies = abs(df["close"] - df["open"])
    return bodies.rolling(period).mean().iloc[-1]


def bullish_displacement(df: pd.DataFrame, multiplier=1.5):
    current_body = candle_body(df["open"].iloc[-1], df["close"].iloc[-1])
    avg_body = average_body(df)

    return (
        df["close"].iloc[-1]
        > df["open"].iloc[-1]
        and current_body > avg_body * multiplier
    )


def bearish_displacement(df: pd.DataFrame, multiplier=1.5):
    current_body = candle_body(df["open"].iloc[-1], df["close"].iloc[-1])
    avg_body = average_body(df)

    return (
        df["close"].iloc[-1]
        < df["open"].iloc[-1]
        and current_body > avg_body * multiplier
    )