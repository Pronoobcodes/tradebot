MAX_TRADES_PER_DAY = 3

MAX_CONSECUTIVE_LOSSES = 2


def can_trade(state):

    if (
        state.trades_today
        >= MAX_TRADES_PER_DAY
    ):
        return False

    if (
        state.consecutive_losses
        >= MAX_CONSECUTIVE_LOSSES
    ):
        return False

    return True