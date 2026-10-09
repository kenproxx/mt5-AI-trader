from types import SimpleNamespace

from app.validation.account_mode import verify_demo_mode


def test_demo_constant_matches():
    mt5 = SimpleNamespace(
        ACCOUNT_TRADE_MODE_DEMO=0,
        account_info=lambda: SimpleNamespace(trade_mode=0),
    )
    assert verify_demo_mode(mt5).verified_demo


def test_live_account_is_blocked():
    mt5 = SimpleNamespace(
        ACCOUNT_TRADE_MODE_DEMO=0,
        account_info=lambda: SimpleNamespace(trade_mode=2),
    )
    assert not verify_demo_mode(mt5).verified_demo


def test_missing_metadata_blocks():
    mt5 = SimpleNamespace(account_info=lambda: None)
    assert not verify_demo_mode(mt5).verified_demo


def test_bool_mode_not_accepted():
    mt5 = SimpleNamespace(
        ACCOUNT_TRADE_MODE_DEMO=0,
        account_info=lambda: SimpleNamespace(trade_mode=False),
    )
    assert not verify_demo_mode(mt5).verified_demo
