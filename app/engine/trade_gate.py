from app.state.state_manager import StateManager

state = StateManager()


def allow_trade():
    return state.can_trade()