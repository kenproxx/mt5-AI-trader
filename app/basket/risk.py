"""Gross exposure and broker-calculated risk; hedges never cancel risk budgets."""
from decimal import Decimal

from app.broker.adapter import dec

D = Decimal


def check_open(adapter, snapshot, decision, config, *, remaining_budget=None):
    if not decision.opens_position or not snapshot.status.eligible:
        return 'INVALID_OPEN'
    a, s, t = snapshot.status.account, snapshot.status.symbol, snapshot.status.tick
    v, sl = decision.lots, decision.stop
    numbers = (a.equity, a.balance, a.free_margin, a.margin, s.volume_min, s.volume_max,
               s.volume_step, s.trade_tick_size, s.point, t.bid, t.ask, v, sl)
    if any(not isinstance(x, Decimal) or not x.is_finite() for x in numbers):
        return 'INVALID_RISK_INPUT'
    if decision.side not in ('BUY', 'SELL') or sl <= 0:
        return 'INVALID_STOP'
    if v < s.volume_min or v > s.volume_max or v % s.volume_step != 0:
        return 'INVALID_VOLUME'
    if len(snapshot.positions) >= config.max_positions:
        return 'POSITION_LIMIT'
    gross = sum((p.lots for p in snapshot.positions), D('0'))
    if gross + v > config.max_total_lots:
        return 'TOTAL_LOT_LIMIT'
    distance = t.bid - sl if decision.side == 'BUY' else sl - t.ask
    if distance <= 0 or distance < s.trade_stops_level * s.point or sl % s.trade_tick_size:
        return 'INVALID_STOP'
    price = t.ask if decision.side == 'BUY' else t.bid
    try:
        loss = -dec(adapter.order_calc_profit(decision.side, s.name, float(v),
                                             float(price), float(sl)))
        loss += v * config.costs_per_lot_usd
        if loss <= 0 or loss > a.equity * D('.005'):
            return 'ORDER_RISK_LIMIT'
        total = loss
        for p in snapshot.positions:
            if (not p.stop.is_finite() or p.stop <= 0
                or p.side == 'BUY' and p.stop >= t.bid
                or p.side == 'SELL' and p.stop <= t.ask):
                return 'POSITION_STOP_INVALID'
            current = t.bid if p.side == 'BUY' else t.ask
            remaining = -dec(adapter.order_calc_profit(p.side, s.name, float(p.lots),
                                                       float(current), float(p.stop)))
            total += max(D('0'), remaining) + p.lots * config.costs_per_lot_usd
        if total > min(a.equity * D('.01'), remaining_budget if remaining_budget is not None else a.equity):
            return 'BASKET_RISK_LIMIT'
        margin = dec(adapter.order_calc_margin(decision.side, s.name, float(v), float(price)))
        if margin <= 0:
            return 'INVALID_MARGIN'
        if a.free_margin - margin < a.equity * D('.3'):
            return 'MARGIN_RESERVE'
        if a.equity * 100 / (a.margin + margin) < config.min_margin_level_pct:
            return 'MARGIN_LEVEL'
    except (ValueError, TypeError, RuntimeError, ArithmeticError):
        return 'BROKER_CALCULATION_FAILED'
    return None
