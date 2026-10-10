"""Read-only Demo XAUUSD feasibility diagnostic; never transmits an order."""
from dataclasses import dataclass
from decimal import Decimal

from app.broker.adapter import dec
from app.broker.models import BrokerState
from app.risk.engine import RiskEngine


@dataclass(frozen=True)
class Feasibility:
    state: BrokerState
    reason: str
    minimum_lot: Decimal = Decimal("0")
    estimated_minimum_margin_usd: Decimal | None = None
    estimated_minimum_stop_loss_usd: Decimal | None = None
    allowed_risk_usd: Decimal | None = None


def inspect_minimum_lot(adapter, status, *, side, stop, costs_usd=Decimal("0")):
    if not status.eligible or status.account is None or status.symbol is None or status.tick is None:
        return Feasibility(BrokerState.NO_TRADE, "Broker compatibility not verified")
    if side not in ("BUY", "SELL"):
        return Feasibility(BrokerState.NO_TRADE, "Invalid side")
    if not isinstance(stop, Decimal) or not isinstance(costs_usd, Decimal):
        return Feasibility(BrokerState.NO_TRADE, "Use Decimal risk inputs")
    if not stop.is_finite() or stop <= 0 or not costs_usd.is_finite() or costs_usd < 0:
        return Feasibility(BrokerState.NO_TRADE, "Invalid stop or costs")
    symbol, account, tick = status.symbol, status.account, status.tick
    entry = tick.ask if side == "BUY" else tick.bid
    if (side == "BUY" and stop >= tick.bid) or (side == "SELL" and stop <= tick.ask):
        return Feasibility(BrokerState.NO_TRADE, "Stop on wrong side")
    if stop % symbol.trade_tick_size != 0:
        return Feasibility(BrokerState.NO_TRADE, "Stop not on tick grid")
    if (tick.bid - stop if side == "BUY" else stop - tick.ask) < symbol.trade_stops_level * symbol.point:
        return Feasibility(BrokerState.NO_TRADE, "Stop below broker minimum distance")
    policy = RiskEngine(adapter).policy
    budget = min(account.equity * policy.target_risk_pct / 100,
                 account.equity * policy.max_risk_pct / 100)
    try:
        profit = dec(adapter.order_calc_profit(side, symbol.name, float(symbol.volume_min),
                                               float(entry), float(stop)))
        margin = dec(adapter.order_calc_margin(side, symbol.name, float(symbol.volume_min),
                                               float(entry)))
    except (ValueError, TypeError, RuntimeError, OverflowError):
        return Feasibility(BrokerState.NO_TRADE, "Broker calculation unavailable")
    loss = -profit + costs_usd
    if loss <= 0 or margin <= 0:
        return Feasibility(BrokerState.NO_TRADE, "Invalid broker calculation")
    reserve = account.equity * policy.min_free_margin_reserve_pct / 100
    if loss > budget:
        state, reason = BrokerState.LOT_BELOW_MINIMUM, "Minimum lot exceeds risk budget"
    elif account.free_margin - margin < reserve:
        state, reason = BrokerState.INSUFFICIENT_MARGIN, "Minimum lot exceeds free margin"
    else:
        state, reason = BrokerState.NO_TRADE, "Estimates pass; full risk checks and order_check required"
    return Feasibility(state, reason, symbol.volume_min, margin, loss, budget)
