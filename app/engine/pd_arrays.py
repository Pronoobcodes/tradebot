"""
pd_arrays.py
------------
Detects all ICT Premium/Discount Arrays:
  - Fair Value Gap (FVG) — BISI and SIBI
  - Order Block (OB) — bullish and bearish
  - Breaker Block
  - Mitigation Block

Priority ranking (strongest to weakest):
  1. Order Block + FVG overlap
  2. Breaker Block
  3. Mitigation Block
  4. FVG alone
  5. S&D zone alone
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class ArrayType(Enum):
    ORDER_BLOCK_PLUS_FVG = "order_block_plus_fvg"   # highest quality
    BREAKER_BLOCK        = "breaker_block"
    MITIGATION_BLOCK     = "mitigation_block"
    FVG                  = "fvg"
    SD_ZONE              = "sd_zone"


class ArrayBias(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"


@dataclass
class FVG:
    """
    Fair Value Gap (3-candle pattern).
    BISI = Buyside Imbalance Sellside Inefficiency (bullish FVG)
    SIBI = Sellside Imbalance Buyside Inefficiency (bearish FVG)
    """
    kind: str                # "BISI" or "SIBI"
    top: float               # upper boundary of the gap
    bottom: float            # lower boundary of the gap
    midpoint: float          # 50% CE (Consequent Encroachment)
    candle_index: int        # index of the middle candle
    candle_time: pd.Timestamp
    filled: bool = False
    partially_filled: bool = False


@dataclass
class OrderBlock:
    """
    ICT Order Block.
    Bullish OB = last down-close candle before an impulse move up.
    Bearish OB = last up-close candle before an impulse move down.
    """
    kind: str                # "bullish" or "bearish"
    ob_high: float
    ob_low: float
    ob_mean: float           # 50% threshold — if price violates this, OB is invalid
    candle_index: int
    candle_time: pd.Timestamp
    has_fvg_above: bool = False   # higher quality if FVG directly above/below
    invalidated: bool = False


@dataclass
class BreakerBlock:
    """
    A failed Order Block that has been broken and flipped.
    Bullish OB that price broke below → becomes bearish Breaker.
    Bearish OB that price broke above → becomes bullish Breaker.
    """
    kind: str                # "bullish_breaker" or "bearish_breaker"
    zone_high: float
    zone_low: float
    candle_index: int
    candle_time: pd.Timestamp


@dataclass
class MitigationBlock:
    """
    Similar to Breaker but formed differently.
    The swing low candles (last down-close before a new low) after a
    failed swing high become the mitigation block.
    """
    kind: str                # "bullish_mitigation" or "bearish_mitigation"
    zone_high: float
    zone_low: float
    candle_index: int
    candle_time: pd.Timestamp


@dataclass
class PDArrayResult:
    """
    Unified result returned to signal_engine.
    Contains the best array found and its quality score.
    """
    array_type: ArrayType
    bias: ArrayBias
    zone_high: float
    zone_low: float
    zone_midpoint: float
    quality_score: int       # 1–5, higher is better
    candle_time: pd.Timestamp
    fvg: Optional[FVG] = None
    order_block: Optional[OrderBlock] = None


# ─────────────────────────────────────────────
# FVG Detection
# ─────────────────────────────────────────────

def detect_fvgs(df: pd.DataFrame, min_gap_pct: float = 0.05) -> list[FVG]:
    """
    Detects all Fair Value Gaps in the dataframe.

    BISI (bullish FVG): candle[i-1].high < candle[i+1].low
      → gap between top of left candle and bottom of right candle
      → price will return to fill this gap

    SIBI (bearish FVG): candle[i-1].low > candle[i+1].high
      → gap between bottom of left candle and top of right candle
    """
    fvgs = []

    for i in range(1, len(df) - 1):
        prev   = df.iloc[i - 1]
        middle = df.iloc[i]
        nxt    = df.iloc[i + 1]

        # BISI: bullish FVG — gap above prev candle, below next candle
        if prev["high"] < nxt["low"]:
            gap_size = nxt["low"] - prev["high"]
            gap_pct  = gap_size / prev["close"] * 100
            if gap_pct >= min_gap_pct:
                fvg = FVG(
                    kind="BISI",
                    bottom=prev["high"],
                    top=nxt["low"],
                    midpoint=(prev["high"] + nxt["low"]) / 2,
                    candle_index=i,
                    candle_time=df.index[i],
                )
                fvgs.append(fvg)

        # SIBI: bearish FVG — gap below prev candle, above next candle
        elif prev["low"] > nxt["high"]:
            gap_size = prev["low"] - nxt["high"]
            gap_pct  = gap_size / prev["close"] * 100
            if gap_pct >= min_gap_pct:
                fvg = FVG(
                    kind="SIBI",
                    top=prev["low"],
                    bottom=nxt["high"],
                    midpoint=(prev["low"] + nxt["high"]) / 2,
                    candle_index=i,
                    candle_time=df.index[i],
                )
                fvgs.append(fvg)

    return fvgs


def check_fvg_filled(fvg: FVG, current_price: float) -> FVG:
    """Check if price has fully or partially filled the FVG."""
    if fvg.kind == "BISI":
        if current_price <= fvg.bottom:
            fvg.filled = True
        elif current_price <= fvg.midpoint:
            fvg.partially_filled = True
    elif fvg.kind == "SIBI":
        if current_price >= fvg.top:
            fvg.filled = True
        elif current_price >= fvg.midpoint:
            fvg.partially_filled = True
    return fvg


def get_nearest_fvg(
    fvgs: list[FVG],
    current_price: float,
    direction: str,     # "long" or "short"
    max_lookback: int = 50,
) -> Optional[FVG]:
    """
    Returns the nearest unfilled FVG in the trade direction.
    For longs: nearest BISI below current price (discount FVG to buy into)
    For shorts: nearest SIBI above current price (premium FVG to sell into)
    """
    recent_fvgs = [f for f in fvgs if not f.filled]
    recent_fvgs = recent_fvgs[-max_lookback:]

    if direction == "long":
        candidates = [f for f in recent_fvgs if f.kind == "BISI" and f.top < current_price]
        if candidates:
            return max(candidates, key=lambda f: f.top)  # closest below
    elif direction == "short":
        candidates = [f for f in recent_fvgs if f.kind == "SIBI" and f.bottom > current_price]
        if candidates:
            return min(candidates, key=lambda f: f.bottom)  # closest above

    return None


# ─────────────────────────────────────────────
# Order Block Detection
# ─────────────────────────────────────────────

def detect_order_blocks(
    df: pd.DataFrame,
    min_impulse_pct: float = 0.1,
    lookback: int = 50,
) -> list[OrderBlock]:
    """
    Detects Order Blocks.

    Bullish OB:
      1. Down-close candle (or consecutive down-close candles)
      2. That candle runs sellside liquidity (makes a new low)
      3. Followed by an impulse move UP that closes above the OB high
      4. Higher quality if a BISI FVG appears directly above

    Bearish OB:
      1. Up-close candle (or consecutive up-close candles)
      2. That candle runs buyside liquidity (makes a new high)
      3. Followed by an impulse move DOWN that closes below the OB low
      4. Higher quality if a SIBI FVG appears directly below
    """
    obs = []
    recent = df.tail(lookback).copy()
    recent = recent.reset_index(drop=False)

    fvgs = detect_fvgs(recent)

    for i in range(2, len(recent) - 2):
        candle  = recent.iloc[i]
        is_down = candle["close"] < candle["open"]
        is_up   = candle["close"] > candle["open"]

        # --- Bullish OB ---
        if is_down:
            # Check if next 1-3 candles make an impulse move up
            impulse_candles = recent.iloc[i+1:i+4]
            if len(impulse_candles) == 0:
                continue
            max_close = impulse_candles["close"].max()
            impulse_pct = (max_close - candle["high"]) / candle["high"] * 100

            if impulse_pct >= min_impulse_pct and max_close > candle["high"]:
                # Check for FVG directly above (displacement)
                has_fvg = any(
                    f.kind == "BISI" and f.bottom >= candle["high"] * 0.999
                    for f in fvgs
                    if f.candle_index > i and f.candle_index <= i + 4
                )
                ob = OrderBlock(
                    kind="bullish",
                    ob_high=candle["high"],
                    ob_low=candle["low"],
                    ob_mean=(candle["high"] + candle["low"]) / 2,
                    candle_index=i,
                    candle_time=recent.iloc[i]["index"] if "index" in recent.columns else df.index[-(lookback - i)],
                    has_fvg_above=has_fvg,
                )
                obs.append(ob)

        # --- Bearish OB ---
        if is_up:
            impulse_candles = recent.iloc[i+1:i+4]
            if len(impulse_candles) == 0:
                continue
            min_close = impulse_candles["close"].min()
            impulse_pct = (candle["low"] - min_close) / candle["low"] * 100

            if impulse_pct >= min_impulse_pct and min_close < candle["low"]:
                has_fvg = any(
                    f.kind == "SIBI" and f.top <= candle["low"] * 1.001
                    for f in fvgs
                    if f.candle_index > i and f.candle_index <= i + 4
                )
                ob = OrderBlock(
                    kind="bearish",
                    ob_high=candle["high"],
                    ob_low=candle["low"],
                    ob_mean=(candle["high"] + candle["low"]) / 2,
                    candle_index=i,
                    candle_time=recent.iloc[i]["index"] if "index" in recent.columns else df.index[-(lookback - i)],
                    has_fvg_above=has_fvg,
                )
                obs.append(ob)

    return obs


def validate_order_block(ob: OrderBlock, current_price: float) -> OrderBlock:
    """
    Invalidates an OB if price has violated the 50% mean threshold.
    From ICT: we do NOT want price to close beyond the midpoint of the OB.
    """
    if ob.kind == "bullish" and current_price < ob.ob_mean:
        ob.invalidated = True
    elif ob.kind == "bearish" and current_price > ob.ob_mean:
        ob.invalidated = True
    return ob


def get_nearest_order_block(
    obs: list[OrderBlock],
    current_price: float,
    direction: str,
) -> Optional[OrderBlock]:
    """Returns nearest valid OB in the trade direction."""
    valid_obs = [o for o in obs if not o.invalidated]

    if direction == "long":
        candidates = [o for o in valid_obs if o.kind == "bullish" and o.ob_high < current_price]
        if candidates:
            return max(candidates, key=lambda o: o.ob_high)
    elif direction == "short":
        candidates = [o for o in valid_obs if o.kind == "bearish" and o.ob_low > current_price]
        if candidates:
            return min(candidates, key=lambda o: o.ob_low)

    return None


# ─────────────────────────────────────────────
# Breaker Block Detection
# ─────────────────────────────────────────────

def detect_breaker_blocks(
    df: pd.DataFrame,
    obs: list[OrderBlock],
    lookback: int = 50,
) -> list[BreakerBlock]:
    """
    A Breaker is a failed Order Block.
    Steps (bearish breaker):
      1. Swing high forms
      2. Swing low forms
      3. Price makes a Higher High (buystops triggered)
      4. Price reverses and breaks BELOW the swing low (sellstops triggered)
      5. The last UP-close candle in the original swing low = Breaker

    When price returns to this zone, it acts as resistance (bearish breaker).
    """
    breakers = []
    current_price = df["close"].iloc[-1]

    for ob in obs:
        ob = validate_order_block(ob, current_price)

        if ob.invalidated:
            # A bullish OB whose mean was violated → potential bearish breaker
            if ob.kind == "bullish":
                breakers.append(BreakerBlock(
                    kind="bearish_breaker",
                    zone_high=ob.ob_high,
                    zone_low=ob.ob_low,
                    candle_index=ob.candle_index,
                    candle_time=ob.candle_time,
                ))
            # A bearish OB whose mean was violated → potential bullish breaker
            elif ob.kind == "bearish":
                breakers.append(BreakerBlock(
                    kind="bullish_breaker",
                    zone_high=ob.ob_high,
                    zone_low=ob.ob_low,
                    candle_index=ob.candle_index,
                    candle_time=ob.candle_time,
                ))

    return breakers


# ─────────────────────────────────────────────
# Best Array Finder — used by signal_engine
# ─────────────────────────────────────────────

def get_best_pd_array(
    df: pd.DataFrame,
    direction: str,        # "long" or "short"
    current_price: float,
) -> Optional[PDArrayResult]:
    """
    Returns the highest-quality PD array for the given direction.
    Priority: OB+FVG > Breaker > Mitigation > FVG > SD zone
    """
    fvgs = detect_fvgs(df)
    obs  = detect_order_blocks(df)
    breakers = detect_breaker_blocks(df, obs)

    # 1. Check for OB + FVG combo (highest quality)
    ob = get_nearest_order_block(obs, current_price, direction)
    if ob and ob.has_fvg_above and not ob.invalidated:
        fvg = get_nearest_fvg(fvgs, current_price, direction)
        return PDArrayResult(
            array_type=ArrayType.ORDER_BLOCK_PLUS_FVG,
            bias=ArrayBias.BULLISH if direction == "long" else ArrayBias.BEARISH,
            zone_high=ob.ob_high,
            zone_low=ob.ob_low,
            zone_midpoint=ob.ob_mean,
            quality_score=5,
            candle_time=ob.candle_time,
            fvg=fvg,
            order_block=ob,
        )

    # 2. Breaker Block
    if direction == "long":
        bullish_breakers = [b for b in breakers if b.kind == "bullish_breaker" and b.zone_high < current_price]
        if bullish_breakers:
            b = max(bullish_breakers, key=lambda x: x.zone_high)
            return PDArrayResult(
                array_type=ArrayType.BREAKER_BLOCK,
                bias=ArrayBias.BULLISH,
                zone_high=b.zone_high,
                zone_low=b.zone_low,
                zone_midpoint=(b.zone_high + b.zone_low) / 2,
                quality_score=4,
                candle_time=b.candle_time,
            )
    elif direction == "short":
        bearish_breakers = [b for b in breakers if b.kind == "bearish_breaker" and b.zone_low > current_price]
        if bearish_breakers:
            b = min(bearish_breakers, key=lambda x: x.zone_low)
            return PDArrayResult(
                array_type=ArrayType.BREAKER_BLOCK,
                bias=ArrayBias.BEARISH,
                zone_high=b.zone_high,
                zone_low=b.zone_low,
                zone_midpoint=(b.zone_high + b.zone_low) / 2,
                quality_score=4,
                candle_time=b.candle_time,
            )

    # 3. Plain Order Block
    if ob and not ob.invalidated:
        return PDArrayResult(
            array_type=ArrayType.ORDER_BLOCK_PLUS_FVG,
            bias=ArrayBias.BULLISH if direction == "long" else ArrayBias.BEARISH,
            zone_high=ob.ob_high,
            zone_low=ob.ob_low,
            zone_midpoint=ob.ob_mean,
            quality_score=3,
            candle_time=ob.candle_time,
            order_block=ob,
        )

    # 4. FVG alone
    fvg = get_nearest_fvg(fvgs, current_price, direction)
    if fvg:
        return PDArrayResult(
            array_type=ArrayType.FVG,
            bias=ArrayBias.BULLISH if direction == "long" else ArrayBias.BEARISH,
            zone_high=fvg.top,
            zone_low=fvg.bottom,
            zone_midpoint=fvg.midpoint,
            quality_score=2,
            candle_time=fvg.candle_time,
            fvg=fvg,
        )

    return None   # No valid array found — no trade
