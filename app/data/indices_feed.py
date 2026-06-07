import time as _time
import pandas as pd
import yfinance as yf

from app.core.logger import logger


INDICES_MAP = {
    "NAS100": "^NDX",
    "SP500": "^GSPC",
}


def _normalize_yfinance_df(df):
    """
    Normalize a yfinance DataFrame to standard columns.

    Handles multi-index columns and various datetime column names
    that yfinance produces across different versions.

    Returns DataFrame with: time, open, high, low, close, volume
    """

    # Handle multi-index columns (yfinance >= 0.2.31)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.reset_index(inplace=True)

    # yfinance names the datetime column differently:
    # 'Datetime' for intraday, 'Date' for daily, or 'index' if unnamed
    datetime_col = None
    for candidate in ["Datetime", "Date", "index"]:
        if candidate in df.columns:
            datetime_col = candidate
            break

    if datetime_col is None:
        # Last resort: use first column
        datetime_col = df.columns[0]

    rename_map = {
        datetime_col: "time",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    }

    # Only rename columns that exist
    rename_map = {k: v for k, v in rename_map.items() if k in df.columns}
    df.rename(columns=rename_map, inplace=True)

    if "volume" not in df.columns:
        df["volume"] = 0

    # Drop Adj Close if present
    if "Adj Close" in df.columns:
        df.drop(columns=["Adj Close"], inplace=True)

    required = ["time", "open", "high", "low", "close", "volume"]
    df = df[required]

    numeric_cols = ["open", "high", "low", "close", "volume"]
    df[numeric_cols] = df[numeric_cols].astype(float)

    return df


def get_indices_data(
    symbol: str,
    interval: str = "1m",
    period: str = "5d",
    retries: int = 3,
):
    """
    Fetch index data from yfinance.

    Returns normalized OHLCV dataframe with columns:
        time, open, high, low, close, volume
    """

    yahoo_symbol = INDICES_MAP.get(symbol)

    if not yahoo_symbol:
        logger.error(
            f"No mapping found for index {symbol}"
        )
        return pd.DataFrame()

    for attempt in range(retries):

        try:
            logger.info(
                f"Fetching index data {symbol}"
            )

            df = yf.download(
                yahoo_symbol,
                period=period,
                interval=interval,
                progress=False,
                auto_adjust=False,
            )

            if df.empty:
                logger.warning(
                    f"No data returned for {symbol}"
                )
                continue

            df = _normalize_yfinance_df(df)

            if len(df) < 50:
                logger.warning(
                    f"Only {len(df)} candles for {symbol} "
                    f"(need 50+)"
                )

            logger.info(
                f"Loaded {len(df)} candles for {symbol}"
            )

            return df

        except Exception as e:
            logger.error(
                f"Attempt {attempt + 1}: "
                f"{symbol} index fetch failed: {e}"
            )
            _time.sleep(2)

    logger.error(
        f"Failed to fetch index data: {symbol}"
    )

    return pd.DataFrame()