"""
Scheduler — Scans all symbols every 5 minutes.

For each symbol:
1. Check if session is active
2. Check if trade gate allows trading
3. Fetch market data (LTF + HTF)
4. Run signal engine
5. If signal found: format → send Telegram → register trade → log
"""

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import SYMBOLS
from app.core.logger import logger
from app.data.feed_router import get_market_data, get_htf_data
from app.engine.rule_engine import RuleEngine, explain_no_signal
from app.state.trade_manager import TradeManager
from app.telegram.notifier import send_message
from app.telegram.formatter import format_signal
from app.analytics.trade_logger import log_trade
from app.core.utils import timestamp

scheduler = BackgroundScheduler()
trade_manager = TradeManager()

def process_symbol(symbol):
    """Process a single symbol through the full pipeline."""

    config = SYMBOLS[symbol]
    sessions = config.get("sessions", [])

    # Instantiate rule engine
    engine = RuleEngine(pair=symbol, trade_manager=trade_manager)

    # ── Fetch data ──
    try:
        df_ltf = get_market_data(symbol)
        df_htf = get_htf_data(symbol)
    except Exception as e:
        logger.error(f"Data fetch failed for {symbol}: {e}")
        return

    if df_ltf is None or df_ltf.empty or df_htf is None or df_htf.empty:
        logger.warning(f"Missing data for {symbol} (LTF or HTF)")
        return

    # ── Generate signal ──
    try:
        signal, layers = engine.evaluate(df_ltf, df_htf, sessions, signal_mode="intraday")
    except Exception as e:
        logger.error(f"Signal engine error for {symbol}: {e}")
        return

    if not signal:
        # We can log why it failed if needed, but typically there's a lot of noise
        # logger.debug(explain_no_signal(layers, symbol))
        return

    # ── Signal found — execute pipeline ──
    logger.info(
        f"SIGNAL: {symbol} {signal.direction} "
        f"Score={signal.quality_score} RR=1:{signal.risk_reward}"
    )

    # Format and send Telegram alert
    message = format_signal(signal)
    send_message(message)

    # Register trade in state manager
    trade_manager.register_trade(
        pair=symbol,
        direction=signal.direction,
        entry=signal.entry_price,
        signal_mode=signal.signal_type,
        data={
            "sl": signal.stop_loss,
            "tp1": signal.take_profit_1,
            "tp2": signal.take_profit_2
        }
    )

    # Log to CSV
    try:
        log_trade({
            "timestamp": signal.timestamp.isoformat(),
            "symbol": symbol,
            "direction": signal.direction,
            "entry": signal.entry_price,
            "sl": signal.stop_loss,
            "tp": signal.take_profit_1, # Using TP1 for logging
            "rr": signal.risk_reward,
            "result": "pending",
            "pnl": 0,
        })
    except Exception as e:
        logger.error(f"Trade logging failed: {e}")


def scan_all():
    """Scan all symbols in a single scheduled job."""

    logger.info(f"--- Scan cycle started at {timestamp()} ---")

    for symbol in SYMBOLS:
        try:
            process_symbol(symbol)
        except Exception as e:
            logger.error(f"Unhandled error processing {symbol}: {e}")

    logger.info("--- Scan cycle complete ---")


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