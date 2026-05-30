def bullish_mss(df):
    last_high = df["High"].iloc[-5:-1].max()
    return df["Close"].iloc[-1] > last_high


def bearish_mss(df):
    last_low = df["Low"].iloc[-5:-1].min()
    return df["Close"].iloc[-1] < last_low