from datetime import datetime


def london_session():
    hour = datetime.utcnow().hour
    return 7 <= hour <= 16


def new_york_session():
    hour = datetime.utcnow().hour
    return 13 <= hour <= 22


def crypto_morning_session():
    hour = datetime.utcnow().hour
    return 0 <= hour <= 12


def session_allowed(session_name: str):
    if session_name == "london":
        return london_session()

    if session_name == "ny":
        return new_york_session()

    if session_name == "crypto_morning":
        return crypto_morning_session()

    return False