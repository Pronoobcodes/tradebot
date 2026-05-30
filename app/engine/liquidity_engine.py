def bullish_sweep(df, lookback=10):
    """
    Detect bullish liquidity sweep.

    Price sweeps below the previous low then closes back above it.
    This signals smart money has taken sell-side liquidity.
    """

    previous_low = df["low"].iloc[-lookback:-1].min()

    current_low = df["low"].iloc[-1]
    current_close = df["close"].iloc[-1]

    return (
        current_low < previous_low
        and current_close > previous_low
    )


def bearish_sweep(df, lookback=10):
    """
    Detect bearish liquidity sweep.

    Price sweeps above the previous high then closes back below it.
    This signals smart money has taken buy-side liquidity.
    """

    previous_high = df["high"].iloc[-lookback:-1].max()

    current_high = df["high"].iloc[-1]
    current_close = df["close"].iloc[-1]

    return (
        current_high > previous_high
        and current_close < previous_high
    )


def get_swept_level(df, direction, lookback=10):
    """
    Return the liquidity level that was swept.

    Used for SL/TP placement.
    """

    if direction == "buy":
        return df["low"].iloc[-lookback:-1].min()
    else:
        return df["high"].iloc[-lookback:-1].max()