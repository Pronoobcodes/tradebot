import time as _time
import pandas as pd
import yfinance as yf

from app.core.logger import logger


INDICES_MAP = {
    "NAS100": "^NDX",
    "SP500": "^GSPC",
}


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

            # Handle yfinance multi-index columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df.reset_index(inplace=True)

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