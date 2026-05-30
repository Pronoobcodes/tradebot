from app.engine.liquidity_engine import bullish_sweep
from app.engine.liquidity_engine import bearish_sweep
from app.engine.market_structure import bullish_mss
from app.engine.market_structure import bearish_mss



def generate_signal(df):

    if bullish_sweep(df) and bullish_mss(df):
        return {
            "direction": "BUY"
        }

    if bearish_sweep(df) and bearish_mss(df):
        return {
            "direction": "SELL"
        }

    return None