from apscheduler.schedulers.background import BackgroundScheduler

from app.config import SYMBOLS
from app.data.feed_router import get_market_data
from app.engine.rule_engine import generate_signal
from app.telegram.notifier import send_message
from app.engine.trade_gate import allow_trade
from app.engine.session_guard import session_allowed


scheduler = BackgroundScheduler()


def process_symbol(symbol):

    config = SYMBOLS[symbol]

    if not session_allowed(config["session"]):
        return

    if not allow_trade():
        return

    df = get_market_data(symbol)

    signal = generate_signal(df)

    if signal:
        send_message(
            f"{symbol} {signal['direction']} SIGNAL"
        )


def start_scheduler():

    for symbol in SYMBOLS:
        scheduler.add_job(
            process_symbol,
            "interval",
            minutes=5,
            args=[symbol],
        )

    scheduler.start()