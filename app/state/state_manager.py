from datetime import date


class StateManager:

    def __init__(self):
        self.active_trade = None
        self.trade_count = 0
        self.current_day = date.today()

    def reset_if_new_day(self):
        today = date.today()

        if today != self.current_day:
            self.trade_count = 0
            self.current_day = today

    def can_trade(self):
        self.reset_if_new_day()

        if self.active_trade:
            return False

        return self.trade_count < 3

    def register_trade(self, trade):
        self.active_trade = trade
        self.trade_count += 1

    def close_trade(self):
        self.active_trade = None