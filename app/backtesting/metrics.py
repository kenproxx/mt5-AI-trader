"""Deterministic metrics; returns are already net of trading costs."""
from decimal import Decimal


def summarize(trade_pnl, initial_equity=Decimal("5")):
    pnl = [Decimal(str(x)) for x in trade_pnl]
    if initial_equity <= 0 or any(not x.is_finite() for x in pnl):
        raise ValueError("Invalid backtest inputs")
    equity = initial_equity
    peak = equity
    max_dd = Decimal("0")
    for value in pnl:
        equity += value
        peak = max(peak, equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak)
    wins = [x for x in pnl if x > 0]
    losses = [x for x in pnl if x < 0]
    gross_profit = sum(wins, Decimal("0"))
    gross_loss = -sum(losses, Decimal("0"))
    return {
        "initial_equity": initial_equity,
        "final_equity": equity,
        "net_profit": sum(pnl, Decimal("0")),
        "trades": len(pnl),
        "win_rate": Decimal(len(wins)) / len(pnl) if pnl else None,
        "profit_factor": gross_profit / gross_loss if gross_loss else None,
        "max_drawdown_pct": max_dd * 100,
        "expectancy": sum(pnl, Decimal("0")) / len(pnl) if pnl else None,
    }
