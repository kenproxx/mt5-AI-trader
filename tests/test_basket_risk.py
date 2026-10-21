from dataclasses import replace
from decimal import Decimal as D

from test_basket_planner import pos, snapshot

from app.basket.config import BasketConfig
from app.basket.models import BasketState
from app.basket.planner import plan
from app.basket.risk import check_open
from app.broker.mock import MockAdapter


def test_five_dollar_account_cannot_force_minimum_lot():
    snap = snapshot()
    snap = replace(snap, status=replace(snap.status, account=replace(
        snap.status.account, equity=D('5'), free_margin=D('5'), balance=D('5'))))
    decision = plan(snap, BasketState(), BasketConfig(), 'BUY')
    assert check_open(MockAdapter(), snap, decision, BasketConfig()) == 'ORDER_RISK_LIMIT'


def test_valid_fixed_lot_passes_without_using_hedge_discount():
    snap = snapshot()
    assert check_open(MockAdapter(), snap, plan(snap, BasketState(), BasketConfig(), 'BUY'),
                      BasketConfig()) is None


def test_gross_lot_cap_counts_both_directions():
    snap = snapshot([pos(lots='.04'), pos(2, 'SELL', '.02', '3000', '3020', '0', 'hedge')])
    d = plan(snapshot(), BasketState(), BasketConfig(), 'BUY')
    assert check_open(MockAdapter(), snap, d, BasketConfig()) == 'TOTAL_LOT_LIMIT'


def test_risk_budget_includes_all_existing_stops_without_offsetting_hedges():
    snap = snapshot([pos(lots='.05', stop='2981')])
    d = plan(snapshot(), BasketState(), BasketConfig(), 'BUY')
    assert check_open(MockAdapter(), snap, d, BasketConfig()) == 'BASKET_RISK_LIMIT'


def test_margin_reserve_rejects_otherwise_valid_order():
    snap = snapshot()
    snap = replace(snap, status=replace(snap.status, account=replace(
        snap.status.account, free_margin=D('3010'))))
    d = plan(snap, BasketState(), BasketConfig(), 'BUY')
    assert check_open(MockAdapter(), snap, d, BasketConfig()) == 'MARGIN_RESERVE'


def test_missing_stop_in_existing_basket_blocks_additions():
    snap = snapshot([pos(stop='0')])
    d = plan(snapshot(), BasketState(), BasketConfig(), 'BUY')
    assert check_open(MockAdapter(), snap, d, BasketConfig()) == 'POSITION_STOP_INVALID'


def test_breached_existing_stop_blocks_new_exposure_until_broker_reconciles():
    snap = snapshot([pos(stop='3001')])
    decision = plan(snapshot(), BasketState(), BasketConfig(), 'BUY')
    assert check_open(MockAdapter(), snap, decision, BasketConfig()) == 'POSITION_STOP_INVALID'
