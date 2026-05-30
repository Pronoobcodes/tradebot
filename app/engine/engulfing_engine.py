import pandas as pd


def bullish_engulfing(df: pd.DataFrame):
    prev_open = df["open"].iloc[-2]
    prev_close = df["close"].iloc[-2]

    curr_open = df["open"].iloc[-1]
    curr_close = df["close"].iloc[-1]

    return (
        prev_close < prev_open
        and curr_close > curr_open
        and curr_open < prev_close
        and curr_close > prev_open
    )


def bearish_engulfing(df: pd.DataFrame):
    prev_open = df["open"].iloc[-2]
    prev_close = df["close"].iloc[-2]

    curr_open = df["open"].iloc[-1]
    curr_close = df["close"].iloc[-1]

    return (
        prev_close > prev_open
        and curr_close < curr_open
        and curr_open > prev_close
        and curr_close < prev_open
    )