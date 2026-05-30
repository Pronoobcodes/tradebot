import csv
import os


LOG_FILE = "trade_log.csv"


def initialize_log():

    if os.path.exists(LOG_FILE):
        return

    with open(
        LOG_FILE,
        "w",
        newline=""
    ) as f:

        writer = csv.writer(f)

        writer.writerow(
            [
                "timestamp",
                "symbol",
                "direction",
                "entry",
                "sl",
                "tp",
                "rr",
                "result",
                "pnl",
            ]
        )


def log_trade(trade):

    initialize_log()

    with open(
        LOG_FILE,
        "a",
        newline=""
    ) as f:

        writer = csv.writer(f)

        writer.writerow(
            [
                trade["timestamp"],
                trade["symbol"],
                trade["direction"],
                trade["entry"],
                trade["sl"],
                trade["tp"],
                trade["rr"],
                trade["result"],
                trade["pnl"],
            ]
        )