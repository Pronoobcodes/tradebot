import ta


def add_indicators(df):

    df["rsi"] = ta.momentum.RSIIndicator(close=df["Close"]).rsi()

    df["ema_50"] = ta.trend.EMAIndicator(close=df["Close"], window=50).ema_indicator()

    return df