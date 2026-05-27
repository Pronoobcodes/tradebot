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
    if df is None or df.empty:
        return False
    
    required_columns = ["timestamp", "open", "high", "low", "close", "volume"]

    for column in required_columns:
        if column not in df.columns:
            return False

    if len(df) < min_rows:
        return False    
    
    return True


def normalize_dataframe(df: pd.DataFrame):
    numeric_columns = ["open", "high", "low", "close", "volume"]
    df[numeric_columns] = df[numeric_columns].astype(float)

    df = df.sort_values(by="timestamp").reset_index(drop=True)
    return df

    
    

    