SPREAD_LIMITS = {
    "BTCUSDT": 10,
    "ETHUSDT": 5,
    "EURGBP": 2,
    "NZDCAD": 3,
    "XAUUSD": 50,
    "NAS100": 40,
    "SP500": 20,
}


def spread_ok(symbol: str, spread: float):

    max_spread = SPREAD_LIMITS.get(symbol, 5)

    return spread <= max_spread