"""Conservative MT5 account mode verification, read-only."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ModeVerification:
    verified_demo: bool
    reason: str


def verify_demo_mode(mt5):
    """Require explicit ACCOUNT_TRADE_MODE_DEMO, never infer from server names."""
    try:
        account = mt5.account_info()
        demo_constant = mt5.ACCOUNT_TRADE_MODE_DEMO
        mode = account.trade_mode
        if type(mode) is not int or type(demo_constant) is not int:
            return ModeVerification(False, "Invalid trade mode metadata")
        if mode != demo_constant:
            return ModeVerification(False, "Account is not verified DEMO")
        return ModeVerification(True, "MT5 account trade mode is DEMO")
    except (AttributeError, TypeError, ValueError, RuntimeError):
        return ModeVerification(False, "Account mode unavailable")
