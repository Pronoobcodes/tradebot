def bullish_sweep(df, lookback=10):
    previous_low = df["Low"].iloc[-lookback:-1].min()

    current_low = df["Low"].iloc[-1]
    current_close = df["Close"].iloc[-1]

    return (
        current_low < previous_low
        and current_close > previous_low
    )


def bearish_sweep(df, lookback=10):
    previous_high = df["High"].iloc[-lookback:-1].max()

    current_high = df["High"].iloc[-1]
    current_close = df["Close"].iloc[-1]

    return (
        current_high > previous_high
        and current_close < previous_high
    )