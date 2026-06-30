"""
session_guard.py
----------------
Checks if the current time is within an active killzone for a given pair.
All times are in EST (Eastern Standard Time / UTC-5).
"""

from datetime import datetime, time, timezone
import pytz

EST = pytz.timezone("America/New_York")

KILLZONES = {
    "asia":         (time(20, 0),  time(0, 0)),   # 8pm – midnight EST
    "london":       (time(2,  0),  time(5, 0)),   # 2am – 5am EST
    "new_york":     (time(7,  0),  time(10, 0)),  # 7am – 10am EST
    "ny_am":        (time(8, 30),  time(12, 0)),  # 8:30am – 12pm EST (indices)
    "london_close": (time(10, 0),  time(12, 0)),  # 10am – 12pm EST
}

PAIR_SESSIONS = {
    "EURUSD": ["london", "new_york"],
    "AUDCAD": ["asia", "london"],
    "NAS100": ["ny_am"],
    "XAUUSD": ["london", "new_york"],
    "SP500":  ["ny_am"],
    "BTCUSDT": ["asia", "london", "new_york"], # Added crypto defaults as an example
    "ETHUSDT": ["asia", "london", "new_york"],
    "EURGBP": ["london"],
    "NZDCAD": ["asia", "london"]
}


def get_est_time() -> datetime:
    return datetime.now(EST)


def _time_in_range(start: time, end: time, check: time) -> bool:
    """Handle overnight ranges too."""
    if start <= end:
        return start <= check <= end
    else:
        return start <= check or check <= end


def is_killzone_active(pair: str, session: str) -> bool:
    """Check if the given session is active right now for the given pair."""
    
    if pair in PAIR_SESSIONS:
        if session not in PAIR_SESSIONS[pair]:
            return False
            
    if session not in KILLZONES:
        return False
        
    start_time, end_time = KILLZONES[session]
    current_time = get_est_time().time()
    
    return _time_in_range(start_time, end_time, current_time)