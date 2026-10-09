from app.validation.readiness import evaluate_readiness


def test_fail_closed_defaults():
    r = evaluate_readiness(
        broker_demo_verified=False, leverage_50_verified=False,
        symbol_verified=False, historical_data_valid=False,
        risk_tests_pass=False, ci_pass=False, forward_demo_validated=False,
    )
    assert not r.demo_research_ready
    assert not r.live_trading_allowed
    assert len(r.blockers) == 7


def test_all_checks_only_allow_demo_research():
    r = evaluate_readiness(
        broker_demo_verified=True, leverage_50_verified=True,
        symbol_verified=True, historical_data_valid=True,
        risk_tests_pass=True, ci_pass=True, forward_demo_validated=True,
    )
    assert r.demo_research_ready
    assert not r.live_trading_allowed


def test_nonboolean_is_not_pass():
    r = evaluate_readiness(
        broker_demo_verified=1, leverage_50_verified=True,
        symbol_verified=True, historical_data_valid=True,
        risk_tests_pass=True, ci_pass=True, forward_demo_validated=True,
    )
    assert "demo_broker_not_verified" in r.blockers
