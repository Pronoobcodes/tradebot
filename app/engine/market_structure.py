"""
market_structure.py
-------------------
Detects:
  - 3-bar swing highs and swing lows (ICT definition)
  - AMD phase (Accumulation, Manipulation, Distribution)
  - Sequential sweep tracker: sweep FIRST, then MSS 1-10 candles later
  - Market Structure Shift (MSS) / Break of Structure (BOS)
  - Higher Timeframe trend direction (bullish / bearish / ranging)
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Bias(Enum):
    BULLISH  = "bullish"
    BEARISH  = "bearish"
    RANGING  = "ranging"


class AMDPhase(Enum):
    ACCUMULATION  = "accumulation"
    MANIPULATION  = "manipulation"
    DISTRIBUTION  = "distribution"
    UNKNOWN       = "unknown"


@dataclass
class SwingPoint:
    index: int
    price: float
    kind: str          # "high" or "low"
    candle_time: pd.Timestamp


@dataclass
class SweepEvent:
    """Recorded when a swing high/low is taken out."""
    index: int
    price: float
    kind: str          # "high_sweep" or "low_sweep"
    candle_time: pd.Timestamp
    confirmed: bool = False   # confirmed once candle closes beyond level


@dataclass
class MSSEvent:
    """Market Structure Shift - candle that breaks opposite structure."""
    index: int
    price: float
    direction: str     # "bullish_mss" or "bearish_mss"
    candle_time: pd.Timestamp
    candles_after_sweep: int   # how many candles after sweep


@dataclass
class SequentialSignal:
    """
    The money signal: sweep happened first, MSS confirmed 1-10 candles later.
    This is what rule_engine.py was incorrectly trying to detect on the same candle.
    """
    sweep: SweepEvent
    mss: MSSEvent
    direction: str     # "long" or "short"
    entry_zone_high: float
    entry_zone_low: float
    valid: bool = True


# ─────────────────────────────────────────────
# Core swing detection (ICT 3-bar definition)
# ─────────────────────────────────────────────

def detect_swing_highs(df: pd.DataFrame, lookback: int = 1) -> list[SwingPoint]:
    """
    A swing high is the candle whose HIGH is higher than `lookback`
    candles to its left AND `lookback` candles to its right.
    ICT uses lookback=1 (3-bar swing).
    """
    swings = []
    for i in range(lookback, len(df) - lookback):
        is_high = all(
            df["high"].iloc[i] > df["high"].iloc[i - j] for j in range(1, lookback + 1)
        ) and all(
            df["high"].iloc[i] > df["high"].iloc[i + j] for j in range(1, lookback + 1)
        )
        if is_high:
            swings.append(SwingPoint(
                index=i,
                price=df["high"].iloc[i],
                kind="high",
                candle_time=df.index[i],
            ))
    return swings


def detect_swing_lows(df: pd.DataFrame, lookback: int = 1) -> list[SwingPoint]:
    """
    A swing low is the candle whose LOW is lower than `lookback`
    candles to its left AND `lookback` candles to its right.
    """
    swings = []
    for i in range(lookback, len(df) - lookback):
        is_low = all(
            df["low"].iloc[i] < df["low"].iloc[i - j] for j in range(1, lookback + 1)
        ) and all(
            df["low"].iloc[i] < df["low"].iloc[i + j] for j in range(1, lookback + 1)
        )
        if is_low:
            swings.append(SwingPoint(
                index=i,
                price=df["low"].iloc[i],
                kind="low",
                candle_time=df.index[i],
            ))
    return swings


# ─────────────────────────────────────────────
# HTF Trend Filter  ← THE KEY FIX
# ─────────────────────────────────────────────

def get_htf_bias(df_htf: pd.DataFrame, swing_lookback: int = 2) -> Bias:
    """
    Determines HTF trend by checking if price is making
    Higher Highs + Higher Lows (bullish) or
    Lower Highs + Lower Lows (bearish).

    df_htf should be 1H or 4H data.
    Only take LTF longs when this returns BULLISH.
    Only take LTF shorts when this returns BEARISH.
    """
    highs = detect_swing_highs(df_htf, lookback=swing_lookback)
    lows  = detect_swing_lows(df_htf,  lookback=swing_lookback)

    if len(highs) < 2 or len(lows) < 2:
        return Bias.RANGING

    # Compare last two swing highs and last two swing lows
    last_two_highs = highs[-2:]
    last_two_lows  = lows[-2:]

    hh = last_two_highs[1].price > last_two_highs[0].price  # Higher High
    hl = last_two_lows[1].price  > last_two_lows[0].price   # Higher Low
    lh = last_two_highs[1].price < last_two_highs[0].price  # Lower High
    ll = last_two_lows[1].price  < last_two_lows[0].price   # Lower Low

    if hh and hl:
        return Bias.BULLISH
    elif lh and ll:
        return Bias.BEARISH
    else:
        return Bias.RANGING


def get_htf_premium_discount(df_htf: pd.DataFrame) -> dict:
    """
    Splits the current dealing range into premium (above 50%) and
    discount (below 50%). Only buy in discount, only sell in premium.
    """
    recent = df_htf.tail(50)
    range_high = recent["high"].max()
    range_low  = recent["low"].min()
    midpoint   = (range_high + range_low) / 2
    current_price = df_htf["close"].iloc[-1]

    zone = "premium" if current_price > midpoint else "discount"
    return {
        "range_high":    range_high,
        "range_low":     range_low,
        "midpoint":      midpoint,
        "current_price": current_price,
        "zone":          zone,
        "pct_position":  (current_price - range_low) / (range_high - range_low) * 100,
    }


# ─────────────────────────────────────────────
# Sequential Sweep → MSS tracker  ← THE MAIN FIX
# ─────────────────────────────────────────────

def detect_liquidity_sweep(
    df: pd.DataFrame,
    swing_points: list[SwingPoint],
    kind: str,           # "high" or "low"
    lookback_candles: int = 30,
) -> Optional[SweepEvent]:
    """
    Detects if the most recent candle took out (swept) a previous
    swing high or swing low WITHOUT closing beyond it (wick sweep).

    A sweep is:
      - For highs: candle HIGH exceeds swing high, but CLOSE is below it
      - For lows:  candle LOW  is below swing low,  but CLOSE is above it

    This is the Judas swing / manipulation phase.
    """
    if not swing_points:
        return None

    current_idx  = len(df) - 1
    current      = df.iloc[-1]
    recent_swings = [s for s in swing_points if s.index > current_idx - lookback_candles]

    if not recent_swings:
        return None

    if kind == "high":
        # Look for the most recent swing high that was swept
        for swing in reversed(recent_swings):
            if swing.index >= current_idx:
                continue
            # Candle wick went above swing high but closed below it
            if current["high"] > swing.price and current["close"] < swing.price:
                return SweepEvent(
                    index=current_idx,
                    price=swing.price,
                    kind="high_sweep",
                    candle_time=df.index[current_idx],
                    confirmed=True,
                )

    elif kind == "low":
        for swing in reversed(recent_swings):
            if swing.index >= current_idx:
                continue
            if current["low"] < swing.price and current["close"] > swing.price:
                return SweepEvent(
                    index=current_idx,
                    price=swing.price,
                    kind="low_sweep",
                    candle_time=df.index[current_idx],
                    confirmed=True,
                )

    return None


def detect_mss(
    df: pd.DataFrame,
    sweep: SweepEvent,
    max_candles_after: int = 10,
) -> Optional[MSSEvent]:
    """
    After a sweep is recorded, watch the NEXT 1–10 candles for a
    Market Structure Shift (MSS).

    After a HIGH sweep (bearish setup):
      MSS = a candle that CLOSES below the most recent swing LOW
      This confirms the manipulation is over and distribution begins.

    After a LOW sweep (bullish setup):
      MSS = a candle that CLOSES above the most recent swing HIGH
      This confirms the manipulation is over and distribution begins.

    This is the FIX: sweep and MSS are on DIFFERENT candles.
    """
    sweep_idx = sweep.index
    search_start = sweep_idx + 1
    search_end   = min(sweep_idx + max_candles_after + 1, len(df))

    if search_start >= len(df):
        return None

    # Find the reference swing point just before the sweep
    swing_highs = detect_swing_highs(df.iloc[:sweep_idx])
    swing_lows  = detect_swing_lows(df.iloc[:sweep_idx])

    if sweep.kind == "high_sweep":
        # Need a recent swing low to break for bearish MSS
        if not swing_lows:
            return None
        reference_low = swing_lows[-1].price

        for i in range(search_start, search_end):
            if i >= len(df):
                break
            candle = df.iloc[i]
            # Bearish MSS: close below the last swing low
            if candle["close"] < reference_low:
                return MSSEvent(
                    index=i,
                    price=candle["close"],
                    direction="bearish_mss",
                    candle_time=df.index[i],
                    candles_after_sweep=i - sweep_idx,
                )

    elif sweep.kind == "low_sweep":
        # Need a recent swing high to break for bullish MSS
        if not swing_highs:
            return None
        reference_high = swing_highs[-1].price

        for i in range(search_start, search_end):
            if i >= len(df):
                break
            candle = df.iloc[i]
            # Bullish MSS: close above the last swing high
            if candle["close"] > reference_high:
                return MSSEvent(
                    index=i,
                    price=candle["close"],
                    direction="bullish_mss",
                    candle_time=df.index[i],
                    candles_after_sweep=i - sweep_idx,
                )

    return None


def build_sequential_signal(
    df_ltf: pd.DataFrame,
    sweep: SweepEvent,
    mss: MSSEvent,
) -> Optional[SequentialSignal]:
    """
    Builds the final SequentialSignal once both sweep and MSS are confirmed.
    The entry zone is the Order Block candle (last candle before the MSS move).
    """
    if mss is None or sweep is None:
        return None

    # The Order Block = last candle before the MSS candle
    ob_idx = mss.index - 1
    if ob_idx < 0 or ob_idx >= len(df_ltf):
        return None

    ob_candle = df_ltf.iloc[ob_idx]

    if mss.direction == "bullish_mss":
        direction = "long"
        # For bullish OB: the last bearish (down-close) candle before the MSS
        entry_high = ob_candle["high"]
        entry_low  = ob_candle["low"]
    else:
        direction = "short"
        # For bearish OB: the last bullish (up-close) candle before the MSS
        entry_high = ob_candle["high"]
        entry_low  = ob_candle["low"]

    return SequentialSignal(
        sweep=sweep,
        mss=mss,
        direction=direction,
        entry_zone_high=entry_high,
        entry_zone_low=entry_low,
        valid=True,
    )


# ─────────────────────────────────────────────
# AMD Phase Detection
# ─────────────────────────────────────────────

def detect_amd_phase(df: pd.DataFrame, window: int = 20) -> AMDPhase:
    """
    Detects the current AMD phase:

    ACCUMULATION  → price ranging, ATR is low, no clear HH/LL
    MANIPULATION  → price just swept a high or low (Judas swing)
    DISTRIBUTION  → MSS confirmed, price expanding in new direction
    """
    recent = df.tail(window)
    price_range = recent["high"].max() - recent["low"].min()
    # atr = (recent["high"] - recent["low"]).mean()

    swing_highs = detect_swing_highs(recent)
    swing_lows  = detect_swing_lows(recent)

    # Check if price is ranging (accumulation)
    range_pct = price_range / recent["close"].mean() * 100
    if range_pct < 0.5 and len(swing_highs) >= 2 and len(swing_lows) >= 2:
        return AMDPhase.ACCUMULATION

    # Check for sweep (manipulation)
    all_highs = detect_swing_highs(df.tail(window * 2))
    all_lows  = detect_swing_lows(df.tail(window * 2))
    high_sweep = detect_liquidity_sweep(df, all_highs, "high")
    low_sweep  = detect_liquidity_sweep(df, all_lows,  "low")

    if high_sweep or low_sweep:
        return AMDPhase.MANIPULATION

    # Otherwise likely in distribution/trending
    return AMDPhase.DISTRIBUTION


# ─────────────────────────────────────────────
# Main entry point for signal_engine
# ─────────────────────────────────────────────

def analyse_structure(
    df_ltf: pd.DataFrame,
    df_htf: pd.DataFrame,
    sweep_lookback: int = 30,
    mss_window: int = 10,
) -> dict:
    """
    Full market structure analysis. Returns dict consumed by signal_engine.py.

    df_ltf → 5m or 15m candles
    df_htf → 1H or 4H candles
    """
    # 1. HTF bias — the gatekeeper
    htf_bias = get_htf_bias(df_htf)
    htf_pd   = get_htf_premium_discount(df_htf)

    # 2. LTF swing points
    ltf_highs = detect_swing_highs(df_ltf)
    ltf_lows  = detect_swing_lows(df_ltf)

    # 3. Detect sweeps
    high_sweep = detect_liquidity_sweep(df_ltf, ltf_highs, "high", sweep_lookback)
    low_sweep  = detect_liquidity_sweep(df_ltf, ltf_lows,  "low",  sweep_lookback)

    # 4. Detect MSS after sweep (sequential — NOT same candle)
    sequential_signal = None
    active_sweep = None

    if high_sweep:
        mss = detect_mss(df_ltf, high_sweep, mss_window)
        if mss:
            sequential_signal = build_sequential_signal(df_ltf, high_sweep, mss)
            active_sweep = high_sweep

    elif low_sweep:
        mss = detect_mss(df_ltf, low_sweep, mss_window)
        if mss:
            sequential_signal = build_sequential_signal(df_ltf, low_sweep, mss)
            active_sweep = low_sweep

    # 5. AMD phase
    amd_phase = detect_amd_phase(df_ltf)

    # 6. HTF filter validation
    # Only allow long signals in bullish HTF + discount zone
    # Only allow short signals in bearish HTF + premium zone
    htf_aligned = False
    if sequential_signal:
        if (sequential_signal.direction == "long"
                and htf_bias == Bias.BULLISH
                and htf_pd["zone"] == "discount"):
            htf_aligned = True
        elif (sequential_signal.direction == "short"
                and htf_bias == Bias.BEARISH
                and htf_pd["zone"] == "premium"):
            htf_aligned = True

    return {
        "htf_bias":           htf_bias.value,
        "htf_zone":           htf_pd["zone"],
        "htf_midpoint":       htf_pd["midpoint"],
        "htf_range_high":     htf_pd["range_high"],
        "htf_range_low":      htf_pd["range_low"],
        "amd_phase":          amd_phase.value,
        "ltf_swing_highs":    ltf_highs,
        "ltf_swing_lows":     ltf_lows,
        "active_sweep":       active_sweep,
        "sequential_signal":  sequential_signal,
        "htf_aligned":        htf_aligned,  # ← if False, no trade
    }