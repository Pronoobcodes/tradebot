from app.config import SYMBOLS
from app.core.logger import logger
from app.data.crypto_feed import get_crypto_data
from app.data.forex_feed import get_forex_data
from app.data.commodities_feed import get_commodities_data
from app.data.indices_feed import get_indices_data


def get_market_data(symbol):
    """
    Route data requests to the correct feed based on asset type.

    Returns a DataFrame with columns:
        time, open, high, low, close, volume
    """

    asset = SYMBOLS.get(symbol)

    if not asset:
        logger.error(f"Unknown symbol: {symbol}")
        return None

    asset_type = asset["type"]
    interval = asset.get("timeframe", "5m")

    try:
        if asset_type == "crypto":
            return get_crypto_data(
                symbol=symbol,
                interval=interval,
            )

        if asset_type == "forex":
            return get_forex_data(
                symbol=symbol,
                interval=interval,
            )

        if asset_type == "commodity":
            return get_commodities_data(
                symbol=symbol,
                interval=interval,
            )

        if asset_type == "index":
            return get_indices_data(
                symbol=symbol,
                interval=interval,
            )

        logger.error(
            f"Unknown asset type '{asset_type}' "
            f"for {symbol}"
        )
        return None

    except Exception as e:
        logger.error(
            f"Feed router error for {symbol}: {e}"
        )
        return None