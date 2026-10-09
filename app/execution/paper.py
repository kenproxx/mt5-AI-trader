"""Paper-only decision engine; no broker write calls."""
from dataclasses import dataclass
from decimal import Decimal

from app.broker.models import BrokerState
from app.risk.engine import RiskEngine


@dataclass(frozen=True)
class PaperDecision:
    state: BrokerState
    reason: str
    side: str
    lots: Decimal = Decimal("0")


def evaluate_paper_signal(adapter, status, signal, stop, costs_usd):
    if signal.side not in ("BUY", "SELL"):
        return PaperDecision(BrokerState.NO_TRADE, signal.reason, "HOLD")
    risk = RiskEngine(adapter).size_order(
        status, side=signal.side, stop=stop, costs_usd=costs_usd
    )
    return PaperDecision(risk.state, risk.reason, signal.side, risk.lots)
