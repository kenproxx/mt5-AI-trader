"""Pure deterministic rules; no broker calls or side effects."""
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal

from app.basket.models import Decision

ZERO = Decimal('0')


def cost(position, config):
    return position.lots * config.costs_per_lot_usd


def plan(snapshot, state, config, signal='HOLD'):
    status = snapshot.status
    if not status.eligible:
        return Decision('HOLD', 'BROKER_INELIGIBLE')
    positions, sym, tick = snapshot.positions, status.symbol, status.tick
    pnl = sum((p.pnl - cost(p, config) for p in positions), ZERO)
    if positions and (state.exiting or pnl <= -status.account.balance * Decimal('.01')
                      or (config.basket_take_profit_usd > 0
                          and pnl >= config.basket_take_profit_usd)):
        # One ticket per cycle: every close is independently checked by MT5.
        return Decision('EXIT', 'BASKET_EXIT', tickets=tuple(p.ticket for p in positions))
    if config.trim_enabled and len(positions) > 1:
        winners = sorted((p for p in positions if p.pnl - cost(p, config) > 0),
                         key=lambda p: p.pnl - cost(p, config), reverse=True)
        losers = sorted((p for p in positions if p.pnl < 0), key=lambda p: p.pnl)
        for winner in winners:
            for loser in losers:
                if winner.pnl + loser.pnl - cost(winner, config) - cost(loser, config) \
                        >= config.trim_buffer_usd:
                    return Decision('TRIM', 'FUNDED_TRIM', tickets=(winner.ticket, loser.ticket))
    if state.last_action and snapshot.now - state.last_action < config.cooldown_seconds:
        return Decision('HOLD', 'COOLDOWN')

    def opening(kind, side, lots):
        price = tick.bid if side == 'BUY' else tick.ask
        distance = max(config.stop_points, Decimal(sym.trade_stops_level + 1)) * sym.point
        stop = price - distance if side == 'BUY' else price + distance
        rounding = ROUND_FLOOR if side == 'BUY' else ROUND_CEILING
        stop = (stop / sym.trade_tick_size).to_integral_value(rounding=rounding) * sym.trade_tick_size
        return Decision(kind, kind, side, lots, stop)

    if not positions:
        if signal in ('BUY', 'SELL'):
            return opening('SEED', signal, config.lot)
        return Decision('HOLD', 'NO_ENTRY_SIGNAL')
    if state.side not in ('BUY', 'SELL') or state.anchor <= 0:
        return Decision('HOLD', 'BASKET_STATE_UNKNOWN')
    primary = [p for p in positions if p.role == 'primary']
    if not primary:
        return Decision('EXIT', 'NO_PRIMARY_REMAINING', tickets=tuple(p.ticket for p in positions))
    close_price = tick.bid if state.side == 'BUY' else tick.ask
    adverse = (state.anchor - close_price) / sym.point * (1 if state.side == 'BUY' else -1)
    layer = state.hedge_count
    if layer < len(config.hedge_points) and adverse >= config.hedge_points[layer]:
        primary_lots = sum((p.lots for p in primary), ZERO)
        hedged_lots = sum((p.lots for p in positions if p.role == 'hedge'), ZERO)
        target = primary_lots * config.hedge_ratios[layer] - hedged_lots
        lots = (target / sym.volume_step).to_integral_value(rounding=ROUND_FLOOR) * sym.volume_step
        if lots >= sym.volume_min:
            return opening('HEDGE', 'SELL' if state.side == 'BUY' else 'BUY', lots)
        return Decision('HOLD', 'HEDGE_BELOW_MINIMUM')
    distances = config.dca_after_points if state.hedged else config.dca_before_points
    index = state.dca_after if state.hedged else state.dca_before
    if index < len(distances) and adverse >= distances[index]:
        return opening('DCA_AFTER' if state.hedged else 'DCA_BEFORE', state.side, config.lot)
    if (not state.hedged and state.pyramid_count < config.max_pyramid_layers
        and signal == state.side and all(p.pnl - cost(p, config) > 0 for p in primary)
        and -adverse >= config.pyramid_step_points * (state.pyramid_count + 1)):
        return opening('PYRAMID', state.side, config.lot)
    return Decision('HOLD', 'NO_LAYER_TRIGGER')
