"""
rule_engine.py  (FIXED VERSION)
--------------------------------
This is the corrected version of rule_engine.py.

THE ORIGINAL BUG:
  The original code checked for a liquidity sweep AND a market structure
  shift (MSS) on the EXACT SAME CANDLE using df.iloc[-1].
  This is nearly impossible in real markets and produced almost zero signals.
  When it did fire (during news spikes), spreads and slippage wiped accounts.

THE FIX — Two changes:
  1. SEQUENTIAL logic: sweep recorded first, MSS watched for over next 1-10 candles
  2. HTF FILTER: only take longs if 1H/4H trend is bullish + price in discount
                 only take shorts if 1H/4H trend is bearish + price in premium

ALL 8 LAYERS must pass before a signal is generated:
  Layer 1 — Killzone active
  Layer 2 — HTF bias aligned (NEW FIX)
  Layer 3 — Price in premium/discount zone (NEW FIX)
  Layer 4 — Liquidity sweep confirmed (previous candles, not current)
  Layer 5 — MSS confirmed AFTER sweep (sequential, not same candle) (NEW FIX)
  Layer 6 — PD Array present at entry zone
  Layer 7 — Entry trigger on LTF (pinbar or engulfing)
  Layer 8 — Trade gate (1 active, max 3/day, daily loss limit)
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone

from app.engine.market_structure import (
    analyse_structure,
    Bias,
    AMDPhase,
    SequentialSignal,
)
from app.engine.pd_arrays import (
    get_best_pd_array,
    PDArrayResult,
    detect_fvgs,
)
from app.engine.session_guard import is_killzone_active
from app.state.trade_manager import TradeManager


# ─────────────────────────────────────────────
# Signal result dataclass
# ─────────────────────────────────────────────

@dataclass
class TradeSignal:
    pair: str
    direction: str           # "long" or "short"
    entry_price: float
    stop_loss: float
    take_profit_1: float     # 1:2 — close 50% here
    take_profit_2: float     # 1:3 — close remaining
    take_profit_swing: Optional[float]  # 1:20+ if swing setup
    risk_reward: float
    signal_type: str         # "intraday" or "swing"
    quality_score: int       # 1–5
    pd_array: str            # which array triggered
    htf_bias: str
    htf_zone: str
    amd_phase: str
    candles_sweep_to_mss: int
    timestamp: datetime
    notes: str = ""


@dataclass
class LayerResult:
    """Tracks which layers passed/failed for debugging."""
    layer_1_killzone: bool = False
    layer_2_htf_bias: bool = False
    layer_3_pd_zone: bool = False
    layer_4_sweep: bool = False
    layer_5_mss_sequential: bool = False
    layer_6_pd_array: bool = False
    layer_7_entry_trigger: bool = False
    layer_8_trade_gate: bool = False

    @property
    def all_pass(self) -> bool:
        return all([
            self.layer_1_killzone,
            self.layer_2_htf_bias,
            self.layer_3_pd_zone,
            self.layer_4_sweep,
            self.layer_5_mss_sequential,
            self.layer_6_pd_array,
            self.layer_7_entry_trigger,
            self.layer_8_trade_gate,
        ])

    def failed_layers(self) -> list[str]:
        failed = []
        if not self.layer_1_killzone:        failed.append("Layer 1: killzone not active")
        if not self.layer_2_htf_bias:        failed.append("Layer 2: HTF bias mismatch")
        if not self.layer_3_pd_zone:         failed.append("Layer 3: wrong premium/discount zone")
        if not self.layer_4_sweep:           failed.append("Layer 4: no liquidity sweep")
        if not self.layer_5_mss_sequential:  failed.append("Layer 5: no sequential MSS after sweep")
        if not self.layer_6_pd_array:        failed.append("Layer 6: no PD array at entry")
        if not self.layer_7_entry_trigger:   failed.append("Layer 7: no entry trigger candle")
        if not self.layer_8_trade_gate:      failed.append("Layer 8: trade gate blocked")
        return failed


# ─────────────────────────────────────────────
# Entry trigger detection (LTF pinbar / engulfing)
# ─────────────────────────────────────────────

def detect_entry_trigger(
    df: pd.DataFrame,
    direction: str,
    zone_high: float,
    zone_low: float,
) -> bool:
    """
    Checks the last 3 candles for a valid entry trigger INSIDE the PD array zone.

    For LONG entries (bullish):
      - Bullish pinbar: long lower wick, small body at top, inside/at zone
      - Bullish engulfing: current close > prev open, both inside/near zone

    For SHORT entries (bearish):
      - Bearish pinbar: long upper wick, small body at bottom
      - Bearish engulfing: current close < prev open
    """
    if len(df) < 3:
        return False

    recent = df.tail(3)
    curr = recent.iloc[-1]
    prev = recent.iloc[-2]

    body_size  = abs(curr["close"] - curr["open"])
    total_size = curr["high"] - curr["low"]
    if total_size == 0:
        return False

    upper_wick = curr["high"] - max(curr["close"], curr["open"])
    lower_wick = min(curr["close"], curr["open"]) - curr["low"]
    body_ratio = body_size / total_size

    # Price must be AT or inside the zone
    price_in_zone = zone_low <= curr["low"] <= zone_high or zone_low <= curr["high"] <= zone_high

    if direction == "long":
        # Bullish pinbar: lower wick >= 2x body, small upper wick
        is_pinbar = (
            lower_wick >= 2 * body_size
            and upper_wick <= body_size
            and body_ratio < 0.4
            and curr["close"] > curr["open"]
        )
        # Bullish engulfing: current candle engulfs previous bearish candle
        is_engulfing = (
            curr["close"] > prev["open"]
            and curr["open"] < prev["close"]
            and prev["close"] < prev["open"]   # prev was bearish
            and curr["close"] > curr["open"]   # current is bullish
        )
        return (is_pinbar or is_engulfing) and price_in_zone

    elif direction == "short":
        # Bearish pinbar: upper wick >= 2x body
        is_pinbar = (
            upper_wick >= 2 * body_size
            and lower_wick <= body_size
            and body_ratio < 0.4
            and curr["close"] < curr["open"]
        )
        # Bearish engulfing
        is_engulfing = (
            curr["close"] < prev["open"]
            and curr["open"] > prev["close"]
            and prev["close"] > prev["open"]   # prev was bullish
            and curr["close"] < curr["open"]   # current is bearish
        )
        return (is_pinbar or is_engulfing) and price_in_zone

    return False


# ─────────────────────────────────────────────
# Risk / SL / TP calculator
# ─────────────────────────────────────────────

def calculate_levels(
    direction: str,
    entry: float,
    pd_array: PDArrayResult,
    sequential_signal: SequentialSignal,
    account_balance: float = 5000,
    risk_pct: float = 0.01,
) -> dict:
    """
    Calculates SL, TP1, TP2, and swing TP.

    SL placement:
      LONG:  just below the OB/zone low (5–10 pip buffer)
      SHORT: just above the OB/zone high (5–10 pip buffer)

    TP1 = 1:2 RR (close 50% of position)
    TP2 = 1:3 RR (close remaining)
    Swing TP = 1:20+ (next HTF liquidity pool)
    """
    buffer_pct = 0.001   # 0.1% buffer beyond zone

    if direction == "long":
        sl = pd_array.zone_low * (1 - buffer_pct)
        risk = entry - sl
        tp1 = entry + (risk * 2)
        tp2 = entry + (risk * 3)
        tp_swing = entry + (risk * 20)
    else:
        sl = pd_array.zone_high * (1 + buffer_pct)
        risk = sl - entry
        tp1 = entry - (risk * 2)
        tp2 = entry - (risk * 3)
        tp_swing = entry - (risk * 20)

    risk_amount   = account_balance * risk_pct
    position_size = risk_amount / risk if risk > 0 else 0

    return {
        "stop_loss":      sl,
        "take_profit_1":  tp1,
        "take_profit_2":  tp2,
        "take_profit_swing": tp_swing,
        "risk_amount":    risk_amount,
        "position_size":  position_size,
        "risk_reward_2":  2.0,
        "risk_reward_3":  3.0,
    }


# ─────────────────────────────────────────────
# THE MAIN RULE ENGINE  (THE FIXED VERSION)
# ─────────────────────────────────────────────

class RuleEngine:
    def __init__(
        self,
        pair: str,
        trade_manager: TradeManager,
        account_balance: float = 5000,
        risk_pct: float = 0.01,
        min_quality_score: int = 2,   # minimum PD array quality to take trade
    ):
        self.pair = pair
        self.tm = trade_manager
        self.account_balance = account_balance
        self.risk_pct = risk_pct
        self.min_quality_score = min_quality_score

    def evaluate(
        self,
        df_ltf: pd.DataFrame,     # 5m or 15m candles
        df_htf: pd.DataFrame,     # 1H or 4H candles
        sessions: list[str],      # e.g. ["london", "new_york"]
        signal_mode: str = "intraday",   # "intraday" or "swing"
    ) -> tuple[Optional[TradeSignal], LayerResult]:
        """
        Runs all 8 layers sequentially.
        Returns (TradeSignal, LayerResult) — signal is None if any layer fails.
        """
        layers = LayerResult()
        
        # Prevent accessing empty dataframes
        if df_ltf is None or df_htf is None or df_ltf.empty or df_htf.empty:
            return None, layers
            
        current_price = df_ltf["close"].iloc[-1]

        # ── LAYER 1: Killzone check ──────────────────────────
        for session in sessions:
            if is_killzone_active(self.pair, session):
                layers.layer_1_killzone = True
                break
                
        if not layers.layer_1_killzone:
            return None, layers

        # ── LAYER 2 + 3: HTF bias + premium/discount ─────────
        # THE KEY FIX: analyse HTF BEFORE looking at LTF signals
        structure = analyse_structure(df_ltf, df_htf)

        htf_bias = structure["htf_bias"]
        htf_zone = structure["htf_zone"]

        # Layer 2: HTF bias must not be ranging
        if htf_bias in ("bullish", "bearish"):
            layers.layer_2_htf_bias = True
        else:
            return None, layers  # Ranging HTF = no trade

        # Layer 3: Price in correct zone for the bias
        if htf_bias == "bullish" and htf_zone == "discount":
            layers.layer_3_pd_zone = True
            candidate_direction = "long"
        elif htf_bias == "bearish" and htf_zone == "premium":
            layers.layer_3_pd_zone = True
            candidate_direction = "short"
        else:
            # Bias and zone mismatch (e.g. bullish but price in premium)
            # Wait — don't force a trade
            return None, layers

        # ── LAYER 4: Liquidity sweep confirmed ───────────────
        # THE FIX: sweep is checked on PAST candles, not just df.iloc[-1]
        sequential_signal: Optional[SequentialSignal] = structure.get("sequential_signal")
        active_sweep = structure.get("active_sweep")

        if active_sweep is not None:
            layers.layer_4_sweep = True
        else:
            return None, layers

        # ── LAYER 5: Sequential MSS (NOT same candle as sweep) ─
        # THE MAIN FIX: MSS must come 1-10 candles AFTER the sweep
        if sequential_signal and sequential_signal.valid:
            # Verify the MSS was NOT on the same candle as the sweep
            if sequential_signal.mss.candles_after_sweep >= 1:
                # Also verify the direction matches HTF bias
                if sequential_signal.direction == candidate_direction:
                    layers.layer_5_mss_sequential = True
                else:
                    return None, layers  # Direction mismatch with HTF
            else:
                # Same candle — this is the original bug — reject it
                return None, layers
        else:
            return None, layers

        # ── LAYER 6: PD Array at entry zone ──────────────────
        pd_result = get_best_pd_array(df_ltf, candidate_direction, current_price)

        if pd_result and pd_result.quality_score >= self.min_quality_score:
            layers.layer_6_pd_array = True
        else:
            return None, layers

        # ── LAYER 7: Entry trigger (pinbar or engulfing) ─────
        if detect_entry_trigger(
            df_ltf,
            candidate_direction,
            pd_result.zone_high,
            pd_result.zone_low,
        ):
            layers.layer_7_entry_trigger = True
        else:
            return None, layers

        # ── LAYER 8: Trade gate ───────────────────────────────
        if self.tm.can_open_trade(self.pair, signal_mode):
            layers.layer_8_trade_gate = True
        else:
            return None, layers

        # ── ALL LAYERS PASSED → Build signal ─────────────────
        levels = calculate_levels(
            direction=candidate_direction,
            entry=current_price,
            pd_array=pd_result,
            sequential_signal=sequential_signal,
            account_balance=self.account_balance,
            risk_pct=self.risk_pct,
        )

        signal = TradeSignal(
            pair=self.pair,
            direction=candidate_direction,
            entry_price=current_price,
            stop_loss=levels["stop_loss"],
            take_profit_1=levels["take_profit_1"],
            take_profit_2=levels["take_profit_2"],
            take_profit_swing=levels["take_profit_swing"] if signal_mode == "swing" else None,
            risk_reward=3.0,
            signal_type=signal_mode,
            quality_score=pd_result.quality_score,
            pd_array=pd_result.array_type.value,
            htf_bias=htf_bias,
            htf_zone=htf_zone,
            amd_phase=structure["amd_phase"],
            candles_sweep_to_mss=sequential_signal.mss.candles_after_sweep,
            timestamp=datetime.now(timezone.utc),
            notes=f"Quality {pd_result.quality_score}/5 | "
                  f"Sweep→MSS: {sequential_signal.mss.candles_after_sweep} candles | "
                  f"Array: {pd_result.array_type.value}",
        )

        return signal, layers


# ─────────────────────────────────────────────
# Quick debug helper
# ─────────────────────────────────────────────

def explain_no_signal(layers: LayerResult, pair: str) -> str:
    """
    Human-readable explanation of why no signal was generated.
    Useful for logging and debugging.
    """
    failed = layers.failed_layers()
    if not failed:
        return f"{pair}: All layers passed — signal generated ✅"
    reason = failed[0]   # first failure stops the chain
    return f"{pair}: No signal — {reason}"