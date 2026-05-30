import pandas as pd

from app.core.utils import average_true_range


def volatility_ok(df: pd.DataFrame, min_atr=0.0001):
    atr = average_true_range(df)
    latest_atr = atr.iloc[-1]
    return latest_atr > min_atr