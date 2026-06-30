"""
Telegram message formatter.

Produces clean, readable signal alerts with all trade details.
"""

def format_signal(signal):
    """
    Format a TradeSignal dataclass into a Telegram message.
    Uses HTML parse mode for bold/italic formatting.
    """
    direction_emoji = "🟢" if signal.direction == "long" else "🔴"
    grade_emoji = {
        5: "💎",
        4: "⭐",
        3: "✅",
        2: "⚠️",
        1: "❌"
    }.get(signal.quality_score, "")

    message = (
        f"{direction_emoji} <b>{signal.pair} — "
        f"{signal.direction.upper()}</b>\n"
        f"\n"
        f"<b>Quality Score:</b> {signal.quality_score}/5 {grade_emoji}\n"
        f"\n"
        f"📍 <b>Entry:</b>  {signal.entry_price:.5f}\n"
        f"🛑 <b>SL:</b>     {signal.stop_loss:.5f}\n"
        f"🎯 <b>TP1 (1:2):</b> {signal.take_profit_1:.5f}\n"
        f"🎯 <b>TP2 (1:3):</b> {signal.take_profit_2:.5f}\n"
    )
    
    if signal.take_profit_swing:
        message += f"🎯 <b>TP Swing:</b> {signal.take_profit_swing:.5f}\n"

    message += (
        f"📊 <b>R:R:</b>    1:{signal.risk_reward}\n"
        f"\n"
        f"<b>Context:</b>\n"
        f"• HTF Bias: {signal.htf_bias}\n"
        f"• HTF Zone: {signal.htf_zone}\n"
        f"• AMD Phase: {signal.amd_phase}\n"
        f"• PD Array: {signal.pd_array}\n"
        f"• Sweep→MSS: {signal.candles_sweep_to_mss} candles\n"
        f"\n"
        f"🕐 {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )

    return message


def format_startup():
    """Format bot startup message."""

    return (
        "🤖 <b>Trading Bot Online</b>\n"
        "\n"
        "✅ Sequential Signal Engine initialized\n"
        "✅ SQLite TradeManager connected\n"
        "✅ Scheduler running (5 min intervals)\n"
        "\n"
        "Monitoring: BTCUSDT, ETHUSDT, EURGBP, "
        "NZDCAD, XAUUSD, NAS100, SP500"
    )


def format_error(symbol, error):
    """Format error notification."""

    return (
        f"⚠️ <b>Error: {symbol}</b>\n"
        f"\n"
        f"{error}"
    )
