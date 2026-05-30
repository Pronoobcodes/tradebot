import time
import pandas as pd
import yfinance as yf

from app.core.logger import logger


FOREX_MAP = {
    "EURGBP": "EURGBP=X",
    "NZDCAD": "NZDCAD=X",
}


def get_forex_data(
    symbol: str,
    interval: str = "5m",
    period: str = "5d",
    retries: int = 3,
):
    """
    Fetch forex data from yfinance.

    Returns normalized OHLCV dataframe with columns:
        time, open, high, low, close, volume
    """

    yahoo_symbol = FOREX_MAP.get(symbol)

    if not yahoo_symbol:
        logger.error(f"No forex mapping found: {symbol}")
        return pd.DataFrame()

    for attempt in range(retries):

        try:
            logger.info(f"Fetching forex data: {symbol}")

            df = yf.download(
                yahoo_symbol,
                period=period,
                interval=interval,
                progress=False,
                auto_adjust=False,
            )

            if df.empty:
                logger.warning(f"Empty forex data: {symbol}")
                continue

            # Handle yfinance multi-index columns (yfinance >= 0.2.31)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df.reset_index(inplace=True)

            # yfinance uses 'Datetime' for intraday, 'Date' for daily
            datetime_col = (
                "Datetime"
                if "Datetime" in df.columns
                else "Date"
            )

            df.rename(
                columns={
                    datetime_col: "time",
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Volume": "volume",
                },
                inplace=True,
            )

            if "volume" not in df.columns:
                df["volume"] = 0

            df = df[
                [
                    "time",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                ]
            ]

            numeric_cols = ["open", "high", "low", "close", "volume"]
            df[numeric_cols] = df[numeric_cols].astype(float)

            logger.info(
                f"Loaded {len(df)} candles for {symbol}"
            )

            return df

        except Exception as e:
            logger.error(
                f"Attempt {attempt + 1}: "
                f"forex fetch failed {symbol}: {e}"
            )
            time.sleep(2)

    logger.error(f"Failed to fetch forex data: {symbol}")
    return pd.DataFrame()