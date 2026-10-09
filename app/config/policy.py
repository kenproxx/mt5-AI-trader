"""Fixed Phase 1 policy. Broker contract terms are always discovered."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class TradingPolicy:
    initial_equity: Decimal = Decimal("5")
    required_leverage: int = 50
    account_currency: str = "USD"
    target_risk_pct: Decimal = Decimal("0.5")
    max_risk_pct: Decimal = Decimal("1")
    max_daily_loss_pct: Decimal = Decimal("2")
    max_weekly_loss_pct: Decimal = Decimal("5")
    min_free_margin_reserve_pct: Decimal = Decimal("30")
    max_open_positions: int = 1
    live_enabled: bool = False
    trading_mode: str = "DEMO"

    def __post_init__(self):
        if self.required_leverage != 50 or self.live_enabled or self.trading_mode != "DEMO":
            raise ValueError("Phase 1 supports only 1:50 DEMO and forbids live trading")
        if not (0 < self.target_risk_pct <= self.max_risk_pct <= 1):
            raise ValueError("Invalid risk policy")
        if not (0 < self.min_free_margin_reserve_pct < 100):
            raise ValueError("Invalid reserve policy")
