import json

from app.basket.worker import main


def test_mock_default_writes_preview_and_blocks_five_dollar_min_lot(tmp_path, capsys):
    status = tmp_path / 'status.json'
    assert main(['--once', '--status-file', str(status)]) == 0
    report = json.loads(status.read_text())
    assert report['mode'] == 'MOCK_PREVIEW'
    assert report['can_place_order'] is False
    assert report['blockers'] == ['ORDER_RISK_LIMIT']
    assert json.loads(capsys.readouterr().out)['action'] == 'SEED'


def test_execute_cannot_be_enabled_in_mock_mode(tmp_path):
    import pytest
    with pytest.raises(SystemExit) as exc:
        main(['--execute-demo', '--account-login', '123', '--once'])
    assert exc.value.code == 2


def test_demo_execution_requires_pinned_login_before_importing_mt5():
    import pytest
    with pytest.raises(SystemExit) as exc:
        main(['--mode', 'mt5', '--execute-demo', '--once'])
    assert exc.value.code == 2


def test_invalid_config_fails_before_importing_mt5(tmp_path):
    import pytest
    path = tmp_path / 'config.json'
    path.write_text('{"max_positions":true}')
    with pytest.raises(SystemExit) as exc:
        main(['--mode', 'mt5', '--config', str(path), '--once'])
    assert exc.value.code == 2
