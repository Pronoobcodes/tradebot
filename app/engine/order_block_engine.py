from dataclasses import dataclass

from app.engine.displacement_engine import (
    bullish_displacement,
    bearish_displacement
)


@dataclass
class OrderBlock:
    ob_type: str
    high: float
    low: float
    valid: bool = True


def bullish_order_block(df):
    if len(df) < 3:
        return None
    previous = df.iloc[-2]
    if (previous["close"] < previous["open"] and bullish_displacement(df)):

        return OrderBlock(
            ob_type="bullish",
            high=previous["high"],
            low=previous["low"]
        )

    return None


def bearish_order_block(df):
    if len(df) < 3:
        return None
    previous = df.iloc[-2]
    if (previous["close"] > previous["open"] and bearish_displacement(df)):

        return OrderBlock(
            ob_type="bearish",
            high=previous["high"],
            low=previous["low"]
        )

    return None