from dataclasses import dataclass
from typing import List


@dataclass
class FVG:
    fvg_type: str
    top: float
    bottom: float
    mitigated: bool = False

active_fvgs: List[FVG] = []


def bullish_fvg(df):
    low = df["low"].iloc[-1]
    high_two = df["high"].iloc[-3]

    if low > high_two:
        return FVG(
            fvg_type="bullish",
            top=low,
            bottom=high_two
        )
    return None


def bearish_fvg(df):
    high = df["high"].iloc[-1]
    low_two = df["low"].iloc[-3]

    if high < low_two:
        return FVG(
            fvg_type="bearish",
            top=low_two,
            bottom=high
        )
    return None


def register_fvg(fvg):
    if fvg:
        active_fvgs.append(fvg)


def check_mitigation(df):
    current_price = df["close"].iloc[-1]
    for fvg in active_fvgs:
        if (fvg.bottom <= current_price <= fvg.top):
            fvg.mitigated = True