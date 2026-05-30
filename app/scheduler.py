"""
Scheduler — Scans all symbols every 5 minutes.

For each symbol:
1. Check if session is active
2. Check if trade gate allows trading
3. Fetch market data
4. Run signal engine
5. If signal found: format → send Telegram → register trade → log
"""

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import SYMBOLS
from app.core.logger import logger
from app.data.feed_router import get_market_data
from app.engine.rule_engine import generate_signal
from app.engine.session_guard import session_allowed
from app.engine.trade_gate import allow_trade, state
from app.telegram.notifier import send_message
from app.telegram.formatter import format_signal
from app.analytics.trade_logger import log_trade
from app.core.utils import timestamp


scheduler = BackgroundScheduler()


def process_symbol(symbol):
    """Process a single symbol through the full pipeline."""

    config = SYMBOLS[symbol]

    # ── Layer 1: Session check ──
    if not session_allowed(config["session"]):
        return

    # ── Layer 2: Trade gate check ──
    if not allow_trade():
        return

    # ── Layer 3: Fetch data ──
    try:
        df = get_market_data(symbol)
    except Exception as e:
        logger.error(f"Data fetch failed for {symbol}: {e}")
        return

    if df is None or df.empty:
        logger.warning(f"No data for {symbol}")
        return

    # ── Layer 4: Generate signal ──
    try:
        signal = generate_signal(df, symbol=symbol)
    except Exception as e:
        logger.error(f"Signal engine error for {symbol}: {e}")
        return

    if not signal:
        return

    # ── Signal found — execute pipeline ──
    logger.info(
        f"SIGNAL: {symbol} {signal['direction']} "
        f"Grade={signal['grade']} RR=1:{signal['rr']}"
    )

    # Format and send Telegram alert
    message = format_signal(signal)
    send_message(message)

    # Register trade in state manager
    state.register_trade({
        "symbol": symbol,
        "direction": signal["direction"],
        "entry": signal["entry"],
        "timestamp": signal["timestamp"],
    })

    # Log to CSV
    try:
        log_trade({
            "timestamp": signal["timestamp"],
            "symbol": symbol,
            "direction": signal["direction"],
            "entry": signal["entry"],
            "sl": signal["stop_loss"],
            "tp": signal["take_profit"],
            "rr": signal["rr"],
            "result": "pending",
            "pnl": 0,
        })
    except Exception as e:
        logger.error(f"Trade logging failed: {e}")


def scan_all():
    """Scan all symbols in a single scheduled job."""

    logger.info(f"── Scan cycle started at {timestamp()} ──")

    for symbol in SYMBOLS:
        try:
            process_symbol(symbol)
        except Exception as e:
            logger.error(f"Unhandled error processing {symbol}: {e}")

    logger.info("── Scan cycle complete ──")


def start_scheduler():
    """Start the background scheduler with a single job scanning all symbols."""

    scheduler.add_job(
        scan_all,
        "interval",
        minutes=5,
        id="market_scanner",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started — scanning every 5 minutes")