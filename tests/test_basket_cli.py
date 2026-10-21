import json
import sys
from datetime import UTC, datetime

import pytest
from basket_fakes import Terminal

from app.basket.worker import main


def test_mock_default_writes_preview_and_blocks_five_dollar_min_lot(tmp_path, capsys):
    status = tmp_path / 'status.json'
    assert main(['--once', '--status-file', str(status)]) == 0
    report = json.loads(status.read_text())
    assert report['mode'] == 'MOCK_PREVIEW'
    assert report['can_place_order'] is False
    assert report['blockers'] == ['ORDER_RISK_LIMIT']
    assert json.loads(capsys.readouterr().out)['action'] == 'SEED'


def test_execute_cannot_be_enabled_in_mock_mode(capsys):
    with pytest.raises(SystemExit) as exc:
        main(['--execute', '--account-login', '123', '--once'])
    assert exc.value.code == 2
    assert 'Execution requires --mode mt5 and --account-login' in capsys.readouterr().err


def test_execution_requires_pinned_login_before_importing_mt5(capsys):
    with pytest.raises(SystemExit) as exc:
        main(['--mode', 'mt5', '--execute', '--once'])
    assert exc.value.code == 2
    assert 'Execution requires --mode mt5 and --account-login' in capsys.readouterr().err


@pytest.mark.parametrize('account_type', [0, 2])
def test_execute_flag_runs_full_basket_pipeline_on_selected_account(tmp_path, monkeypatch, account_type):
    class MarketTerminal(Terminal):
        TIMEFRAME_M1 = 60
        TIMEFRAME_M5 = 300
        TIMEFRAME_M15 = 900
        TIMEFRAME_H1 = 3600

        def copy_rates_from_pos(self, symbol, timeframe, start, count):
            last = self.tick.time - self.tick.time % timeframe - timeframe
            return [dict(time=last - (count - 1 - i) * timeframe,
                open=3000 + i * .01, close=3000 + i * .01,
                high=3000.5 + i * .01, low=2999.5 + i * .01) for i in range(count)]

    terminal = MarketTerminal()
    terminal.account.trade_mode = account_type

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.fromtimestamp(terminal.tick.time, UTC).astimezone(tz)

    monkeypatch.setitem(sys.modules, 'MetaTrader5', terminal)
    monkeypatch.setattr('app.basket.runner.datetime', Clock)
    monkeypatch.setattr('app.basket.gateway.time.time', lambda: terminal.tick.time)
    status = tmp_path / 'status.json'
    args = ['--mode', 'mt5', '--account-login', '123', '--once',
            '--state-file', str(tmp_path / 'state.sqlite3'), '--status-file', str(status)]
    assert main(args) == 0
    assert json.loads(status.read_text())['mode'] == 'MT5_PREVIEW'
    assert not terminal.sent
    assert main([*args, '--execute']) == 0
    report = json.loads(status.read_text())
    assert report['mode'] == 'MT5_EXECUTION'
    assert report['execution'] == 'FILLED'
    assert report['signal'] == 'BUY'
    assert len(terminal.positions) == 1
    assert terminal.positions[0].sl > 0


def test_old_demo_only_flag_is_not_silently_reinterpreted(capsys):
    with pytest.raises(SystemExit) as exc:
        main(['--mode', 'mt5', '--account-login', '123', '--execute-demo', '--once'])
    assert exc.value.code == 2
    assert 'unrecognized arguments: --execute-demo' in capsys.readouterr().err


def test_invalid_config_fails_before_importing_mt5(tmp_path):
    path = tmp_path / 'config.json'
    path.write_text('{"max_positions":true}')
    with pytest.raises(SystemExit) as exc:
        main(['--mode', 'mt5', '--config', str(path), '--once'])
    assert exc.value.code == 2
