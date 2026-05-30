from dataclasses import dataclass

from app.engine.engulfing_engine import (
    bullish_engulfing,
    bearish_engulfing,
)

from app.engine.displacement_engine import (
    bullish_displacement,
    bearish_displacement,
)

from app.engine.volatility_guard import volatility_ok
from app.engine.fvg_engine import bullish_fvg, bearish_fvg
from app.engine.order_block_engine import (
    bullish_order_block,
    bearish_order_block,
)


@dataclass
class SignalScore:
    score: int
    direction: str
    details: dict


def score_signal(df, direction):
    """
    Score a signal based on multiple confluence factors.

    Points breakdown:
        Liquidity sweep + MSS = prerequisite (handled by rule_engine)
        Engulfing candle    = +20
        Displacement candle = +25
        FVG present         = +20
        Order Block present = +20
        Volatility ok       = +15

    Minimum score for trade: 40
    """

    score = 0
    details = {}

    if direction == "buy":
        if bullish_engulfing(df):
            score += 20
            details["engulfing"] = True

        if bullish_displacement(df):
            score += 25
            details["displacement"] = True

        fvg = bullish_fvg(df)
        if fvg:
            score += 20
            details["fvg"] = {
                "top": fvg.top,
                "bottom": fvg.bottom,
            }

        ob = bullish_order_block(df)
        if ob:
            score += 20
            details["order_block"] = {
                "high": ob.high,
                "low": ob.low,
            }

    elif direction == "sell":
        if bearish_engulfing(df):
            score += 20
            details["engulfing"] = True

        if bearish_displacement(df):
            score += 25
            details["displacement"] = True

        fvg = bearish_fvg(df)
        if fvg:
            score += 20
            details["fvg"] = {
                "top": fvg.top,
                "bottom": fvg.bottom,
            }

        ob = bearish_order_block(df)
        if ob:
            score += 20
            details["order_block"] = {
                "high": ob.high,
                "low": ob.low,
            }

    if volatility_ok(df):
        score += 15
        details["volatility"] = True

    return SignalScore(
        score=score,
        direction=direction,
        details=details,
    )


def trade_quality(score):
    """Grade the signal quality."""

    if score >= 80:
        return "A+"
    if score >= 60:
        return "A"
    if score >= 40:
        return "B"
    return "C"


# Minimum score to take a trade
MIN_SCORE = 40