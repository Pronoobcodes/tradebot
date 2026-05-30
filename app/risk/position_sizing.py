def calculate_position_size(balance, risk_percent, stop_loss_pips, pip_value,):

    risk_amount = (balance * risk_percent / 100)

    lot_size = (risk_amount / ( stop_loss_pips * pip_value))

    return round(
        lot_size,
        2
    )