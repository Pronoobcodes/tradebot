from dataclasses import dataclass

from app.engine.engulfing_engine import (
    bullish_engulfing,
    bearish_engulfing,
)

from app.engine.displacement_engine import (
    bullish_displacement,
    bearish_displacement,
)

from app.engine.volatility_guard import volatility_ok,


@dataclass
class SignalScore:
    score: int
    direction: str


def bullish_score(df):
    score = 0
    if bullish_engulfing(df):
        score += 20

    if bullish_displacement(df):
        score += 25

    if volatility_ok(df):
        score += 15

    return SignalScore(
        score=score,
        direction="buy"
    )


def bearish_score(df):
    score = 0

    if bearish_engulfing(df):
        score += 20

    if bearish_displacement(df):
        score += 25

    if volatility_ok(df):
        score += 15

    return SignalScore(
        score=score,
        direction="sell"
    )


def trade_quality(score):
    if score >= 80:
        return "A+"

    if score >= 60:
        return "A"

    if score >= 40:
        return "B"

    return "C"