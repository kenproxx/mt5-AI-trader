from dataclasses import asdict
from decimal import Decimal as D
from types import SimpleNamespace as NS

import pytest
from basket_fakes import Terminal

from app.basket.config import BasketConfig
from app.basket.gateway import DemoGateway
from app.basket.journal import Journal
from app.basket.models import BasketState
from app.basket.runner import BasketRunner


def runner(tmp_path, terminal=None, login=123):
    terminal = terminal or Terminal()
    cfg = BasketConfig()
    return BasketRunner(DemoGateway(terminal, cfg, expected_login=login, clock=lambda: terminal.tick.time),
                        tmp_path / 'basket.sqlite3', cfg), terminal


def cycle(r, t, execute=True, signal='BUY'):
    return r.cycle(now=t.tick.time, signal=signal, execute=execute)


def test_preview_never_sends_but_reports_decision(tmp_path):
    r, t = runner(tmp_path)
    report = cycle(r, t, execute=False)
    assert report['action'] == 'SEED'
    assert report['execution'] == 'PREVIEW'
    assert not t.sent


def test_demo_seed_records_ticket_and_does_not_duplicate_after_restart(tmp_path):
    r, t = runner(tmp_path)
    assert cycle(r, t)['execution'] == 'FILLED'
    assert t.sent[0]['sl'] == 2980
    assert t.sent[0]['type_filling'] == 0
    r2, _ = runner(tmp_path, t)
    assert cycle(r2, t)['action'] == 'HOLD'
    assert len(t.sent) == 1


@pytest.mark.parametrize(('field', 'bad'), [('trade_mode', 2), ('trade_mode', False),
    ('margin_mode', 0), ('leverage', 100), ('currency', 'EUR'), ('hedge_allowed', False),
    ('fifo_close', True), ('login', 456)])
def test_wrong_account_never_sends(tmp_path, field, bad):
    r, t = runner(tmp_path)
    setattr(t.account, field, bad)
    assert cycle(r, t)['execution'] == 'BLOCKED'
    assert not t.sent


def test_execute_requires_explicit_account_login(tmp_path):
    r, t = runner(tmp_path, login=None)
    assert cycle(r, t)['execution'] == 'BLOCKED'
    assert not t.sent


def test_broker_check_refusal_does_not_send(tmp_path):
    r, t = runner(tmp_path)
    t.check_code = 10019
    assert cycle(r, t)['execution'] == 'BLOCKED'
    assert not t.sent


@pytest.mark.parametrize('mode', ['timeout', 'partial'])
def test_uncertain_outcome_latches_journal_and_never_retries(tmp_path, mode):
    r, t = runner(tmp_path)
    t.send_mode = mode
    assert cycle(r, t)['execution'] == 'BLOCKED'
    t.send_mode = 'done'
    r2, _ = runner(tmp_path, t)
    report = cycle(r2, t)
    assert 'PENDING_EXECUTION_REVIEW' in report['blockers']
    assert len(t.sent) == 1


def test_foreign_position_and_pending_order_block(tmp_path):
    r, t = runner(tmp_path)
    t.orders = [NS(ticket=9)]
    assert cycle(r, t)['execution'] == 'BLOCKED'
    t.orders = []
    t.positions = [NS(ticket=9, magic=1234, symbol='XAUUSD')]
    assert cycle(r, t)['execution'] == 'BLOCKED'
    assert not t.sent


def test_missing_journal_with_existing_bot_position_does_not_adopt(tmp_path):
    r, t = runner(tmp_path)
    cycle(r, t)
    r.path.unlink()
    assert cycle(r, t)['execution'] == 'BLOCKED'
    assert len(t.sent) == 1


def test_cannot_change_config_or_account_on_same_state(tmp_path):
    r, t = runner(tmp_path)
    cycle(r, t, execute=False)
    t.account.login = 456
    r.gateway.expected_login = 456
    assert cycle(r, t)['execution'] == 'BLOCKED'
    assert not t.sent


def test_journal_lock_rejects_second_process_handle(tmp_path):
    path = tmp_path / 'state.sqlite3'
    with Journal(path):
        with pytest.raises((ValueError, OSError)):
            with Journal(path):
                pass


def prepare_trim(tmp_path, realized):
    r, t = runner(tmp_path)
    cycle(r, t)
    # Seed a second confirmed test position and its durable ownership.
    t.positions[0].profit = 5
    t.positions.append(NS(ticket=200, magic=r.config.magic, symbol='XAUUSD',
        type=0, volume=.01, price_open=3000, sl=2980, profit=-3, swap=0))
    with Journal(r.path) as journal:
        data = journal.load()
        data['state']['tickets']['200'] = 'primary'
        data['state']['last_action'] = 0
        journal.save(data)
    t.realized_override = realized
    return r, t


def test_trim_closes_winner_then_loser_using_realized_history(tmp_path):
    r, t = prepare_trim(tmp_path, 5)
    report = cycle(r, t, signal='HOLD')
    assert report['execution'] == 'FILLED'
    assert [x['position'] for x in t.sent[1:]] == [101, 200]
    assert not t.positions


def test_trim_does_not_spend_unrealized_or_missing_profit(tmp_path):
    r, t = prepare_trim(tmp_path, 1)
    report = cycle(r, t, signal='HOLD')
    assert report['execution'] == 'TRIM_WINNER_ONLY'
    assert [x.ticket for x in t.positions] == [200]
    assert len(t.sent) == 2


def test_exits_still_run_after_day_entry_lock(tmp_path):
    r, t = runner(tmp_path)
    cycle(r, t)
    t.account.equity = 9700
    t.positions[0].profit = -300
    assert cycle(r, t, signal='HOLD')['action'] == 'EXIT'
    assert not t.positions


def test_cashflow_after_start_blocks_new_entries(tmp_path):
    r, t = runner(tmp_path)
    cycle(r, t, execute=False)
    t.tick.time += 61
    t.deals.append(NS(type=2, time=t.tick.time))
    assert 'CASHFLOW_REVIEW' in cycle(r, t)['blockers']
    assert not t.sent


def test_corrupt_state_does_not_reset(tmp_path):
    r, t = runner(tmp_path)
    with Journal(r.path) as journal:
        journal.save({'state': asdict(BasketState(anchor=D('NaN')))})
    assert cycle(r, t)['execution'] == 'BLOCKED'
    assert not t.sent


def test_equity_can_move_between_account_reads_without_being_an_identity_change(tmp_path):
    class MovingEquity(Terminal):
        reads = 0
        def account_info(self):
            self.reads += 1
            return NS(**{**vars(self.account), 'equity': 10000 + self.reads / 100})
    r, t = runner(tmp_path, MovingEquity())
    assert cycle(r, t, execute=False)['execution'] == 'PREVIEW'


def test_different_journals_cannot_execute_same_account_concurrently(tmp_path):
    r, t = runner(tmp_path)
    other, _ = runner(tmp_path / 'other', t)
    original = t.order_check
    child_results = []
    def check(request):
        if not child_results:
            child_results.append(None)
            child_results[0] = cycle(other, t)
        return original(request)
    t.order_check = check
    assert cycle(r, t)['execution'] == 'FILLED'
    assert child_results[0]['execution'] == 'BLOCKED'
    assert len(t.sent) == 1


def test_position_profit_can_move_between_reads_without_blocking_dca(tmp_path):
    r, t = runner(tmp_path)
    cycle(r, t)
    t.tick.time += 61
    t.tick.bid, t.tick.ask = 2997, 2997.2
    reads = [0]
    def moving_positions():
        reads[0] += 1
        return [NS(**{**vars(p), 'profit': -3 - reads[0] / 100}) for p in t.positions]
    t.positions_get = moving_positions
    report = cycle(r, t)
    assert report['action'] == 'DCA_BEFORE'
    assert report['execution'] == 'FILLED'
    assert len(t.sent) == 2


def test_spread_widening_during_order_check_blocks_before_send(tmp_path):
    r, t = runner(tmp_path)
    original = t.order_check
    def widen(request):
        result = original(request)
        t.tick.ask = 3002
        return result
    t.order_check = widen
    assert cycle(r, t)['execution'] == 'BLOCKED'
    assert not t.sent


def test_real_send_clock_rejects_tick_that_aged_during_order_check(tmp_path):
    r, t = runner(tmp_path)
    clock = [t.tick.time]
    r.gateway.clock = lambda: clock[0]
    original = t.order_check
    def slow_check(request):
        result = original(request)
        clock[0] += 60
        return result
    t.order_check = slow_check
    assert cycle(r, t)['execution'] == 'BLOCKED'
    assert not t.sent


def test_trim_rechecks_funding_after_loser_order_check(tmp_path):
    r, t = prepare_trim(tmp_path, 5)
    original = t.order_check
    def adverse(request):
        result = original(request)
        if request.get('position') == 200:
            next(p for p in t.positions if p.ticket == 200).profit = -10
        return result
    t.order_check = adverse
    assert cycle(r, t, signal='HOLD')['execution'] == 'BLOCKED'
    assert [p.ticket for p in t.positions] == [200]
    assert len(t.sent) == 2


def test_exit_tries_other_ticket_when_first_close_would_consume_reserved_margin(tmp_path):
    r, t = runner(tmp_path)
    cycle(r, t)
    t.positions = [NS(ticket=102, magic=r.config.magic, symbol='XAUUSD', type=1,
                      volume=.01, price_open=2994, sl=3014, profit=0, swap=0),
                   NS(ticket=103, magic=r.config.magic, symbol='XAUUSD', type=0,
                      volume=.02, price_open=2990, sl=2970, profit=0, swap=0)]
    t.account.margin_free = 3100
    t.account.margin = 6900
    with Journal(r.path) as journal:
        data = journal.load()
        data['state'].update(exiting=True, hedged=True, tickets={'102': 'hedge', '103': 'primary'})
        journal.save(data)
    checked = []
    def margin_check(request):
        checked.append(request['position'])
        free = 2900 if request['position'] == 102 else 4000
        return NS(retcode=0, equity=10000, margin=10000-free, margin_free=free)
    t.order_check = margin_check
    assert cycle(r, t, signal='HOLD')['execution'] == 'FILLED'
    assert checked == [102, 103]
    assert t.sent[-1]['position'] == 103


def test_equity_move_during_check_reduces_remaining_daily_budget(tmp_path):
    r, t = runner(tmp_path)
    original = t.order_check
    def reduce_equity(request):
        result = original(request)
        t.account.equity = 9820
        return result
    t.order_check = reduce_equity
    report = cycle(r, t)
    assert report['execution'] == 'BLOCKED'
    assert report['blockers'] == ['BASKET_RISK_LIMIT']
    assert not t.sent


def test_complete_hedge_dca_cycle_preserves_layer_counts_across_restart(tmp_path):
    r, t = runner(tmp_path)
    # Synthetic capital large enough for all five layers under the 1% gross SL budget.
    t.account.equity = t.account.balance = t.account.margin_free = 20000
    expected = ['SEED', 'DCA_BEFORE', 'HEDGE', 'DCA_AFTER', 'HEDGE']
    for bid, want in zip([3000, 2997, 2994, 2991, 2988], expected, strict=True):
        t.tick.bid, t.tick.ask = bid, bid + .2
        t.tick.time += 61
        report = cycle(r, t)
        assert (report['action'], report['execution']) == (want, 'FILLED'), report
        r, _ = runner(tmp_path, t)
    assert [x['volume'] for x in t.sent] == [.01, .01, .01, .01, .02]
    with Journal(r.path) as journal:
        state = journal.load()['state']
        assert (state['dca_before'], state['dca_after'], state['hedge_count']) == (1, 1, 2)
    t.tick.bid, t.tick.ask = 2985, 2985.2
    t.tick.time += 61
    assert cycle(r, t)['blockers'] == ['TOTAL_LOT_LIMIT']
    assert len(t.sent) == 5
