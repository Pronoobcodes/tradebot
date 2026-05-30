from app.risk.position_sizing import (
    calculate_position_size
)


class RiskManager:

    def __init__(self):

        self.max_risk = 1

    def position_size(
        self,
        balance,
        stop_loss,
        pip_value,
    ):

        return calculate_position_size(
            balance,
            self.max_risk,
            stop_loss,
            pip_value,
        )