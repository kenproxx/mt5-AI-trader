"""Read-only MT5 Demo diagnostics. No order_send or order_check."""
from dataclasses import asdict, dataclass
from decimal import Decimal

from app.broker.compatibility import CompatibilityChecker
from app.broker.models import BrokerState
from app.validation.demo_feasibility import inspect_minimum_lot


@dataclass(frozen=True)
class DemoDiagnostic:
    state: str
    reason: str
    broker_server: str | None = None
    leverage: int | None = None
    account_currency: str | None = None
    account_equity_usd: str | None = None
    symbol: str | None = None
    volume_min: str | None = None
    margin_min_lot_usd: str | None = None
    stop_loss_min_lot_usd: str | None = None
    risk_budget_usd: str | None = None

    def public_dict(self):
        return asdict(self)


def run_demo_diagnostic(adapter, *, side, stop, costs_usd=Decimal("0"),
                        now_epoch=None):
    status = CompatibilityChecker(adapter).inspect(now_epoch=now_epoch)
    if not status.eligible:
        return DemoDiagnostic(status.state.value, status.reason)
    account, symbol = status.account, status.symbol
    # A server name alone cannot establish DEMO account mode.
    # Block until the caller independently verifies demo mode.
    result = inspect_minimum_lot(
        adapter, status, side=side, stop=stop, costs_usd=costs_usd,
    )
    return DemoDiagnostic(
        state=result.state.value,
        reason=result.reason + "; DEMO mode not independently verified",
        broker_server=account.server,
        leverage=account.leverage,
        account_currency=account.currency,
        account_equity_usd=str(account.equity),
        symbol=symbol.name,
        volume_min=str(symbol.volume_min),
        margin_min_lot_usd=(
            str(result.estimated_minimum_margin_usd)
            if result.estimated_minimum_margin_usd is not None else None
        ),
        stop_loss_min_lot_usd=(
            str(result.estimated_minimum_stop_loss_usd)
            if result.estimated_minimum_stop_loss_usd is not None else None
        ),
        risk_budget_usd=(
            str(result.allowed_risk_usd)
            if result.allowed_risk_usd is not None else None
        ),
    )
