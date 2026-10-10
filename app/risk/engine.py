"""Strict broker-calculated sizing; no order transmission."""
from dataclasses import dataclass
from decimal import Decimal

from app.broker.adapter import dec
from app.broker.models import BrokerState
from app.config.policy import TradingPolicy


@dataclass(frozen=True)
class RiskDecision:
    state: BrokerState
    reason: str
    lots: Decimal = Decimal("0")
    estimated_loss_usd: Decimal = Decimal("0")
    required_margin_usd: Decimal = Decimal("0")

    @property
    def allowed(self):
        return self.state == BrokerState.TRADE_ELIGIBLE


class RiskEngine:
    def __init__(self, adapter, policy=None):
        self.adapter = adapter
        self.policy = policy or TradingPolicy()

    def size_order(
        self, status, *, side, stop, costs_usd,
        daily_loss_usd=Decimal("0"), weekly_loss_usd=Decimal("0"),
        open_positions=0, daily_start_equity=None, weekly_start_equity=None,
    ):
        def reject(state, reason):
            return RiskDecision(state, reason)

        if not status.eligible or status.symbol is None or status.tick is None or status.account is None:
            return reject(BrokerState.NO_TRADE, "Broker not eligible")
        if side not in ("BUY", "SELL"):
            return reject(BrokerState.NO_TRADE, "Invalid side")
        if type(open_positions) is not int or open_positions < 0 or open_positions >= self.policy.max_open_positions:
            return reject(BrokerState.RISK_LIMIT_EXCEEDED, "Position limit")
        sym, tick, acct = status.symbol, status.tick, status.account
        values = (stop, costs_usd, daily_loss_usd, weekly_loss_usd)
        if any(not isinstance(x, Decimal) or not x.is_finite() for x in values):
            return reject(BrokerState.NO_TRADE, "Invalid risk input types")
        if stop <= 0 or costs_usd < 0:
            return reject(BrokerState.NO_TRADE, "Invalid risk inputs")
        entry = tick.ask if side == "BUY" else tick.bid
        if (side == "BUY" and stop >= tick.bid) or (side == "SELL" and stop <= tick.ask):
            return reject(BrokerState.NO_TRADE, "Invalid SL side")
        distance = tick.bid - stop if side == "BUY" else stop - tick.ask
        if stop % sym.trade_tick_size != 0 or distance < sym.trade_stops_level * sym.point:
            return reject(BrokerState.NO_TRADE, "SL too close or wrong tick grid")
        day_base = daily_start_equity if daily_start_equity is not None else acct.equity
        week_base = weekly_start_equity if weekly_start_equity is not None else acct.equity
        if (any(not isinstance(x, Decimal) or not x.is_finite() for x in (day_base, week_base))
            or day_base <= 0 or week_base <= 0 or daily_loss_usd < 0 or weekly_loss_usd < 0):
            return reject(BrokerState.NO_TRADE, "Invalid loss baseline")
        daily_cap = day_base * self.policy.max_daily_loss_pct / 100
        weekly_cap = week_base * self.policy.max_weekly_loss_pct / 100
        if daily_loss_usd >= daily_cap or weekly_loss_usd >= weekly_cap:
            return reject(BrokerState.RISK_LIMIT_EXCEEDED, "Period loss guard")
        budget = min(
            acct.equity * self.policy.target_risk_pct / 100,
            acct.equity * self.policy.max_risk_pct / 100,
            daily_cap - daily_loss_usd,
            weekly_cap - weekly_loss_usd,
        )
        if budget <= 0:
            return reject(BrokerState.RISK_LIMIT_EXCEEDED, "No risk budget")
        selected = None
        size = sym.volume_min
        for _ in range(100000):
            if size > sym.volume_max:
                break
            try:
                p = self.adapter.order_calc_profit(side, sym.name, float(size), float(entry), float(stop))
                loss = -dec(p) + costs_usd
            except (ValueError, TypeError, RuntimeError, OverflowError):
                return reject(BrokerState.NO_TRADE, "Profit estimate failed")
            if loss <= 0:
                return reject(BrokerState.NO_TRADE, "Nonpositive expected stop loss")
            if loss > budget:
                break
            selected = (size, loss)
            size += sym.volume_step
        if selected is None:
            return reject(BrokerState.LOT_BELOW_MINIMUM, "Minimum lot exceeds risk")
        lots, loss = selected
        try:
            margin = dec(self.adapter.order_calc_margin(side, sym.name, float(lots), float(entry)))
        except (ValueError, TypeError, RuntimeError, OverflowError):
            return reject(BrokerState.NO_TRADE, "Margin estimate failed")
        reserve = acct.equity * self.policy.min_free_margin_reserve_pct / 100
        if margin <= 0:
            return reject(BrokerState.NO_TRADE, "Invalid margin estimate")
        if acct.free_margin - margin < reserve:
            return reject(BrokerState.INSUFFICIENT_MARGIN, "Insufficient margin reserve")
        return RiskDecision(BrokerState.TRADE_ELIGIBLE, "Risk passes; order_check still required", lots, loss, margin)
