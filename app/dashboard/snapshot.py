"""Read-only dashboard snapshot: safe fields only, no order endpoints."""
from dataclasses import dataclass
from decimal import Decimal

from app.backtesting.metrics import summarize
from app.monitoring.health import assess_health


@dataclass(frozen=True)
class DashboardSnapshot:
    mode: str
    healthy: bool
    blockers: tuple[str, ...]
    trades: int
    net_profit_usd: str
    max_drawdown_pct: str


def build_snapshot(*, mode, broker_connected, data_fresh, risk_ready, trade_pnl):
    if mode != "DEMO":
        raise ValueError("Dashboard supports DEMO only")
    health = assess_health(
        broker_connected=broker_connected,
        data_fresh=data_fresh,
        risk_ready=risk_ready,
        demo_account=True,
    )
    metrics = summarize(trade_pnl, initial_equity=Decimal("5"))
    return DashboardSnapshot(
        mode=mode,
        healthy=health.healthy,
        blockers=health.reasons,
        trades=metrics["trades"],
        net_profit_usd=str(metrics["net_profit"]),
        max_drawdown_pct=str(metrics["max_drawdown_pct"]),
    )
