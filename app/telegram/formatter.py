"""
Telegram message formatter.

Produces clean, readable signal alerts with all trade details.
"""


def format_signal(signal):
    """
    Format a signal dict into a Telegram message.

    Uses HTML parse mode for bold/italic formatting.
    """

    direction_emoji = "🟢" if signal["direction"] == "BUY" else "🔴"
    grade_emoji = {
        "A+": "💎",
        "A": "⭐",
        "B": "✅",
        "C": "⚠️",
    }.get(signal["grade"], "")

    # Build confluence list
    confluence_parts = []
    details = signal.get("confluence", {})

    if details.get("engulfing"):
        confluence_parts.append("• Engulfing candle")

    if details.get("displacement"):
        confluence_parts.append("• Displacement")

    fvg = details.get("fvg")
    if fvg:
        confluence_parts.append(
            f"• FVG ({fvg['bottom']:.5f} – {fvg['top']:.5f})"
        )

    ob = details.get("order_block")
    if ob:
        confluence_parts.append(
            f"• Order Block ({ob['low']:.5f} – {ob['high']:.5f})"
        )

    if details.get("volatility"):
        confluence_parts.append("• Volatility ✓")

    confluence_text = "\n".join(confluence_parts) if confluence_parts else "—"

    message = (
        f"{direction_emoji} <b>{signal['symbol']} — "
        f"{signal['direction']}</b>\n"
        f"\n"
        f"<b>Grade:</b> {signal['grade']} {grade_emoji} "
        f"(Score: {signal['score']})\n"
        f"\n"
        f"📍 <b>Entry:</b>  {signal['entry']}\n"
        f"🛑 <b>SL:</b>     {signal['stop_loss']}\n"
        f"🎯 <b>TP:</b>     {signal['take_profit']}\n"
        f"📊 <b>R:R:</b>    1:{signal['rr']}\n"
        f"\n"
        f"<b>Confluence:</b>\n"
        f"{confluence_text}\n"
        f"\n"
        f"🕐 {signal['timestamp']}"
    )

    return message


def format_startup():
    """Format bot startup message."""

    return (
        "🤖 <b>Trading Bot Online</b>\n"
        "\n"
        "✅ All engines initialized\n"
        "✅ Data feeds connected\n"
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
