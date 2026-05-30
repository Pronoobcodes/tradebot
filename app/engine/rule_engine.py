"""
Signal Engine — 8-Layer Signal Checklist

Every signal must pass ALL layers:
1. Session active (handled by scheduler before calling this)
2. Liquidity sweep detected
3. Market structure shift confirmed
4. FVG or Order Block confluence
5. Displacement or engulfing confirmation
6. Scoring quality gate (minimum score)
7. Risk/reward calculation
8. Trade gate (handled by scheduler after this returns)
"""

from app.core.logger import logger
from app.core.utils import timestamp

from app.engine.liquidity_engine import (
    bullish_sweep,
    bearish_sweep,
    get_swept_level,
)
from app.engine.market_structure import (
    bullish_mss,
    bearish_mss,
)
from app.engine.scoring_engine import (
    score_signal,
    trade_quality,
    MIN_SCORE,
)


def _calculate_levels(df, direction, rr_target=3.0):
    """
    Calculate entry, stop loss, and take profit levels.

    For BUY:  SL below the swept low, TP at RR multiple above entry
    For SELL: SL above the swept high, TP at RR multiple below entry
    """

    entry = df["close"].iloc[-1]
    swept_level = get_swept_level(df, direction)

    if direction == "buy":
        # SL just below the swept low with a small buffer
        atr_buffer = (df["high"].iloc[-1] - df["low"].iloc[-1]) * 0.2
        stop_loss = swept_level - atr_buffer
        risk = entry - stop_loss

        if risk <= 0:
            return None

        take_profit = entry + (risk * rr_target)

    else:
        atr_buffer = (df["high"].iloc[-1] - df["low"].iloc[-1]) * 0.2
        stop_loss = swept_level + atr_buffer
        risk = stop_loss - entry

        if risk <= 0:
            return None

        take_profit = entry - (risk * rr_target)

    rr = round(abs(take_profit - entry) / abs(entry - stop_loss), 2)

    return {
        "entry": round(entry, 5),
        "stop_loss": round(stop_loss, 5),
        "take_profit": round(take_profit, 5),
        "rr": rr,
    }


def generate_signal(df, symbol="UNKNOWN"):
    """
    Run the full signal checklist on a DataFrame.

    Returns a signal dict if all layers pass, or None if no signal.
    """

    if df is None or df.empty or len(df) < 20:
        return None

    try:
        # ── Layer 1: Check for BULLISH setup ──
        if bullish_sweep(df) and bullish_mss(df):
            direction = "buy"

            # ── Layer 2: Score confluence ──
            signal_score = score_signal(df, direction)

            if signal_score.score < MIN_SCORE:
                logger.info(
                    f"{symbol} BUY signal too weak: "
                    f"score={signal_score.score}"
                )
                return None

            # ── Layer 3: Calculate trade levels ──
            levels = _calculate_levels(df, direction)

            if not levels:
                logger.info(
                    f"{symbol} BUY invalid risk levels"
                )
                return None

            grade = trade_quality(signal_score.score)

            return {
                "symbol": symbol,
                "direction": "BUY",
                "entry": levels["entry"],
                "stop_loss": levels["stop_loss"],
                "take_profit": levels["take_profit"],
                "rr": levels["rr"],
                "score": signal_score.score,
                "grade": grade,
                "confluence": signal_score.details,
                "timestamp": timestamp(),
            }

        # ── Layer 1: Check for BEARISH setup ──
        if bearish_sweep(df) and bearish_mss(df):
            direction = "sell"

            # ── Layer 2: Score confluence ──
            signal_score = score_signal(df, direction)

            if signal_score.score < MIN_SCORE:
                logger.info(
                    f"{symbol} SELL signal too weak: "
                    f"score={signal_score.score}"
                )
                return None

            # ── Layer 3: Calculate trade levels ──
            levels = _calculate_levels(df, direction)

            if not levels:
                logger.info(
                    f"{symbol} SELL invalid risk levels"
                )
                return None

            grade = trade_quality(signal_score.score)

            return {
                "symbol": symbol,
                "direction": "SELL",
                "entry": levels["entry"],
                "stop_loss": levels["stop_loss"],
                "take_profit": levels["take_profit"],
                "rr": levels["rr"],
                "score": signal_score.score,
                "grade": grade,
                "confluence": signal_score.details,
                "timestamp": timestamp(),
            }

    except Exception as e:
        logger.error(
            f"Signal engine error for {symbol}: {e}"
        )
        return None

    return None