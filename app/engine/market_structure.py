def bullish_mss(df, lookback=5):
    """
    Detect bullish market structure shift.

    Current close breaks above the highest high of the last N candles.
    Indicates a shift from bearish to bullish.
    """

    last_high = df["high"].iloc[-lookback - 1:-1].max()
    return df["close"].iloc[-1] > last_high


def bearish_mss(df, lookback=5):
    """
    Detect bearish market structure shift.

    Current close breaks below the lowest low of the last N candles.
    Indicates a shift from bullish to bearish.
    """

    last_low = df["low"].iloc[-lookback - 1:-1].min()
    return df["close"].iloc[-1] < last_low