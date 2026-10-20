"""Independent VTrade-style controls: no calls that can place an MT5 order."""
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.automation.guards import (
    GuardSettings,
    evaluate_guards,
    update_periods,
)
from app.automation.scanner import read_closed_candles
from app.automation.state import load_state, save_state
from app.automation.worker import inspect_once
from app.broker.mock import MockAdapter

FINGERPRINT = "a" * 64
WEDNESDAY = datetime(2026, 10, 21, 12, tzinfo=UTC)
EQUITY = Decimal("5")


def new_state(now=WEDNESDAY):
    return update_periods(None, account_fingerprint=FINGERPRINT, equity=EQUITY, now=now)


def inspect(state, equity=EQUITY, spread=Decimal("10"), now=WEDNESDAY, positions=0,
            settings=None):
    return evaluate_guards(
        state, equity=equity, spread_points=spread,
        open_positions=positions, now=now, broker_eligible=True, settings=settings,
    )


def test_spread_blocks_entry_without_changing_equity_locks():
    result = inspect(new_state(), spread=Decimal("51"))
    assert result.reasons == ("SPREAD_FILTER",)
    assert not result.state.day_locked


def test_weekend_and_friday_cutoff_block_new_entries():
    state = new_state()
    friday = datetime(2026, 10, 23, 20, tzinfo=UTC)
    assert "WEEKEND_LOCK" in inspect(state, now=friday).reasons
    sunday = datetime(2026, 10, 25, 10, tzinfo=UTC)
    assert "WEEKEND_LOCK" in inspect(state, now=sunday).reasons


def test_daily_loss_is_latched_until_next_utc_day():
    state = new_state()
    loss = inspect(state, equity=Decimal("4.89"))
    assert loss.state.day_locked and not loss.allowed
    recovered = inspect(loss.state, equity=Decimal("5.2"))
    assert "DAY_TARGET_OR_LOSS_LOCK" in recovered.reasons
    tomorrow = WEDNESDAY + timedelta(days=1)
    next_state = update_periods(
        recovered.state, account_fingerprint=FINGERPRINT,
        equity=Decimal("5.2"), now=tomorrow,
    )
    assert not next_state.day_locked


def test_weekly_peak_drawdown_stays_locked_after_recovery():
    state = new_state()
    raised = update_periods(
        state, account_fingerprint=FINGERPRINT,
        equity=Decimal("5.5"), now=WEDNESDAY,
    )
    lost = inspect(raised, equity=Decimal("5.1"))
    assert lost.week_drawdown_pct > Decimal("5")
    assert lost.state.week_locked
    assert "WEEK_LOSS_OR_DRAWDOWN_LOCK" in inspect(
        lost.state, equity=Decimal("5.6"),
    ).reasons


def test_daily_profit_target_opt_in():
    state = new_state()
    enabled = GuardSettings(daily_profit_target_pct=Decimal("1"))
    assert inspect(state, equity=Decimal("5.06"), settings=enabled).state.day_locked
    assert inspect(state, equity=Decimal("5.06")).allowed


def test_unknown_positions_and_spread_fail_closed():
    state = new_state()
    with pytest.raises(ValueError):
        inspect(state, positions=-1)
    with pytest.raises(ValueError):
        inspect(state, spread=Decimal("NaN"))


def test_different_account_or_clock_rollback_is_rejected():
    state = new_state()
    with pytest.raises(ValueError):
        update_periods(state, account_fingerprint="b" * 64, equity=EQUITY, now=WEDNESDAY)
    with pytest.raises(ValueError):
        update_periods(
            state, account_fingerprint=FINGERPRINT,
            equity=EQUITY, now=WEDNESDAY - timedelta(days=1),
        )


def test_guard_state_round_trip_and_corruption(tmp_path):
    path = tmp_path / "guard.json"
    assert load_state(path) is None
    state = new_state()
    save_state(path, state)
    assert load_state(path) == state
    path.write_text('{"schema":1}', encoding="utf-8")
    with pytest.raises(ValueError):
        load_state(path)


def test_closed_bars_reject_forming_and_stale():
    now = 1900000020  # Exact multiple of 60
    now -= now % 60

    class MT5:
        TIMEFRAME_M1 = 1

        def __init__(self, last):
            self.last = last

        def copy_rates_from_pos(self, symbol, timeframe, start, count):
            assert symbol == "XAUUSD" and timeframe == 1 and start == 1
            return [
                {"time": self.last - (219 - i) * 60, "open": 3000, "high": 3001,
                 "low": 2999, "close": 3000} for i in range(220)
            ]

    good = MT5(now - 60)
    assert len(read_closed_candles(good, "XAUUSD", "M1", now_epoch=now)) == 220
    with pytest.raises(ValueError):
        read_closed_candles(MT5(now), "XAUUSD", "M1", now_epoch=now)
    with pytest.raises(ValueError):
        read_closed_candles(MT5(now - 600), "XAUUSD", "M1", now_epoch=now)


def test_mock_worker_never_places_orders(tmp_path):
    adapter = MockAdapter()
    report = inspect_once(
        adapter, state_file=tmp_path / "guard.json",
        settings=GuardSettings(), costs_usd=Decimal("0.01"),
        now=datetime.fromtimestamp(adapter.tick.time, UTC),
    )
    assert not report["can_place_order"]
    assert not report["entry_allowed"]
    assert report["blockers"] == ["TERMINAL_REQUIRED"]


def test_closed_bar_signal_is_paper_only_and_sized_to_affordable_lot(tmp_path):
    # Illustrative synthetic account, NOT evidence of feasible $5 XAUUSD trading.
    from dataclasses import replace
    from types import SimpleNamespace

    adapter = MockAdapter()
    adapter.account = replace(
        adapter.account, equity=Decimal("1000"), free_margin=Decimal("1000"),
        balance=Decimal("1000"),
    )
    adapter.tick = replace(adapter.tick, time=int(WEDNESDAY.timestamp()))

    class FakeTerminal:
        ACCOUNT_TRADE_MODE_DEMO = 0
        TIMEFRAME_M1 = 1
        TIMEFRAME_M5 = 5
        TIMEFRAME_M15 = 15
        TIMEFRAME_H1 = 60

        def account_info(self):
            return SimpleNamespace(login=123, trade_mode=0)

        def positions_get(self):
            return ()

        def copy_rates_from_pos(self, symbol, timeframe, start, count):
            seconds = {1: 60, 5: 300, 15: 900, 60: 3600}[timeframe]
            now_epoch = int(WEDNESDAY.timestamp())
            last = now_epoch - now_epoch % seconds - seconds
            return [
                {"time": last - (219 - i) * seconds,
                 "open": 3000 + i * 0.01, "close": 3000 + i * 0.01,
                 "high": 3000.5 + i * 0.01, "low": 2999.5 + i * 0.01}
                for i in range(220)
            ]

    adapter.mt5 = FakeTerminal()
    report = inspect_once(
        adapter, state_file=tmp_path / "state.json",
        settings=GuardSettings(), costs_usd=Decimal("0.01"), now=WEDNESDAY,
    )
    assert report["entry_allowed"]
    assert report["signal"] == "BUY"
    assert report["paper_lots"] == "0.01"
    assert not report["can_place_order"]
    assert (tmp_path / "state.json").exists()
