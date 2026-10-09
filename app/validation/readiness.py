"""Final validation checklist: conservative DEMO-only readiness."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Readiness:
    demo_research_ready: bool
    blockers: tuple[str, ...]
    live_trading_allowed: bool = False


def evaluate_readiness(*, broker_demo_verified, leverage_50_verified,
                       symbol_verified, historical_data_valid,
                       risk_tests_pass, ci_pass, forward_demo_validated):
    checks = {
        "demo_broker_not_verified": broker_demo_verified,
        "leverage_not_1_to_50": leverage_50_verified,
        "symbol_contract_not_verified": symbol_verified,
        "historical_data_invalid": historical_data_valid,
        "risk_tests_not_passed": risk_tests_pass,
        "ci_not_passed": ci_pass,
        "forward_demo_not_validated": forward_demo_validated,
    }
    blockers = tuple(key for key, passed in checks.items() if passed is not True)
    return Readiness(not blockers, blockers)
