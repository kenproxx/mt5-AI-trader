from dataclasses import replace
from decimal import Decimal as D

import pytest

from app.basket.config import BasketConfig
from app.basket.models import BasketState, Position, Snapshot
from app.basket.planner import plan
from app.broker.compatibility import CompatibilityChecker
from app.broker.mock import MockAdapter


def snapshot(positions=(), bid='3000', ask='3000.2'):
    broker = MockAdapter()
    broker.account = replace(broker.account, equity=D('10000'), free_margin=D('10000'),
                             balance=D('10000'), margin=D('0'))
    broker.tick = replace(broker.tick, bid=D(bid), ask=D(ask))
    status = CompatibilityChecker(broker).inspect(now_epoch=broker.tick.time)
    return Snapshot(status, tuple(positions), 'a' * 64, broker.tick.time)


def pos(ticket=1, side='BUY', lots='.02', entry='3000', stop='2980', pnl='-6', role='primary'):
    return Position(ticket, side, D(lots), D(entry), D(stop), D(pnl), role)


def state(**kwargs):
    return replace(BasketState(side='BUY', anchor=D('3000')), **kwargs)


def test_seed_has_fixed_lot_and_stop():
    d = plan(snapshot(), BasketState(), BasketConfig(), 'BUY')
    assert (d.kind, d.side, d.lots, d.stop) == ('SEED', 'BUY', D('.01'), D('2980'))


def test_no_signal_no_seed():
    assert plan(snapshot(), BasketState(), BasketConfig(), 'HOLD').kind == 'HOLD'


@pytest.mark.parametrize(('side', 'bid', 'ask'), [('BUY', '2997', '2997.2'),
                                               ('SELL', '3002.8', '3003')])
def test_dca_before_hedge_is_symmetric(side, bid, ask):
    p = pos(side=side, stop='3020' if side == 'SELL' else '2980')
    d = plan(snapshot([p], bid, ask), state(side=side), BasketConfig(), side)
    assert (d.kind, d.side, d.lots) == ('DCA_BEFORE', side, D('.01'))


def test_hedge_priority_and_fraction_of_primary_exposure():
    d = plan(snapshot([pos()], '2994', '2994.2'), state(), BasketConfig(), 'BUY')
    assert (d.kind, d.side, d.lots) == ('HEDGE', 'SELL', D('.01'))


def test_second_hedge_tops_up_to_target_without_overhedging():
    snap = snapshot([pos(), pos(2, 'SELL', '.01', '2994', '3014', '6', 'hedge')],
                    '2988', '2988.2')
    d = plan(snap, state(hedged=True, hedge_count=1), BasketConfig(), 'BUY')
    assert (d.kind, d.lots) == ('HEDGE', D('.01'))


def test_post_hedge_dca_uses_separate_threshold_and_counter():
    cfg = replace(BasketConfig(), trim_enabled=False)
    d = plan(snapshot([pos()], '2991', '2991.2'),
             state(hedged=True, hedge_count=1, dca_before=1), cfg, 'HOLD')
    assert d.kind == 'DCA_AFTER'
    assert plan(snapshot([pos()], '2991', '2991.2'),
                state(hedged=True, hedge_count=1, dca_after=1), cfg, 'BUY').kind == 'HOLD'


def test_pyramid_requires_every_primary_profitable_and_matching_signal():
    snap = snapshot([pos(pnl='6')], '3003', '3003.2')
    assert plan(snap, state(), BasketConfig(), 'BUY').kind == 'PYRAMID'
    assert plan(snap, state(), BasketConfig(), 'SELL').kind == 'HOLD'
    assert plan(snapshot([pos(pnl='6'), pos(2, pnl='-1')], '3003', '3003.2'),
                state(), replace(BasketConfig(), trim_enabled=False), 'BUY').kind == 'HOLD'
    assert plan(snap, state(hedged=True), BasketConfig(), 'BUY').kind == 'HOLD'


def test_trim_plans_winner_before_loser_and_requires_cost_buffer():
    snap = snapshot([pos(1, pnl='5'), pos(2, pnl='-3')])
    d = plan(snap, state(), BasketConfig(), 'HOLD')
    assert d.kind == 'TRIM'
    assert d.tickets == (1, 2)
    assert plan(snapshot([pos(1, pnl='3'), pos(2, pnl='-3')]), state(),
                BasketConfig(), 'HOLD').kind == 'HOLD'


def test_exit_latches_take_priority_over_new_layers():
    d = plan(snapshot([pos()], '2994', '2994.2'), state(exiting=True), BasketConfig(), 'BUY')
    assert d.kind == 'EXIT'
    assert d.tickets == (1,)


def test_loss_limit_closes_basket_even_without_entry_signal():
    d = plan(snapshot([pos(pnl='-100')]), state(), BasketConfig(), 'HOLD')
    assert d.kind == 'EXIT'


def test_layer_counter_does_not_recreate_closed_layer():
    snap = snapshot([pos()], '2997', '2997.2')
    assert plan(snap, state(dca_before=1), BasketConfig(), 'BUY').kind == 'HOLD'


@pytest.mark.parametrize('changes', [dict(lot=D('NaN')), dict(lot=D('0')),
    dict(max_positions=True), dict(max_total_lots=D('Infinity')),
    dict(hedge_ratios=(D('1.5'),)), dict(dca_before_points=(D('600'), D('300')))])
def test_bad_config_fails_closed(changes):
    with pytest.raises(ValueError):
        replace(BasketConfig(), **changes)
