"""VTrade-inspired entry guards; independent design, DEMO research only.

No broker writes, trade execution, grid, or martingale are implemented here.
"""
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal

from app.config.policy import TradingPolicy


@dataclass(frozen=True)
class GuardSettings:
    max_spread_points: Decimal = Decimal("50")
    max_weekly_drawdown_pct: Decimal = Decimal("5")
    daily_profit_target_pct: Decimal = Decimal("0")  # Disabled unless explicitly configured.
    friday_lock_hour_utc: int = 20

    def __post_init__(self):
        for value in (
            self.max_spread_points,
            self.max_weekly_drawdown_pct,
            self.daily_profit_target_pct,
        ):
            if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
                raise ValueError("Invalid guard threshold")
        if self.max_spread_points <= 0 or self.max_weekly_drawdown_pct <= 0:
            raise ValueError("Guards must be positive")
        if not isinstance(self.friday_lock_hour_utc, int) or not (
            0 <= self.friday_lock_hour_utc <= 23
        ):
            raise ValueError("Invalid Friday UTC hour")


@dataclass(frozen=True)
class GuardState:
    account_fingerprint: str
    day: str
    week: str
    day_start_equity: Decimal
    week_start_equity: Decimal
    week_peak_equity: Decimal
    day_locked: bool = False
    week_locked: bool = False


@dataclass(frozen=True)
class GuardResult:
    allowed: bool
    reasons: tuple[str, ...]
    state: GuardState
    day_pnl_pct: Decimal
    week_loss_usd: Decimal
    day_loss_usd: Decimal
    week_drawdown_pct: Decimal


def _equity(value):
    if not isinstance(value, Decimal) or not value.is_finite() or value <= 0:
        raise ValueError("Equity must be a positive finite Decimal")
    return value


def update_periods(
    previous: GuardState | None, *, account_fingerprint: str, equity: Decimal, now: datetime
) -> GuardState:
    _equity(equity)
    if not account_fingerprint or len(account_fingerprint) != 64:
        raise ValueError("Missing account identity")
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Timezone-aware UTC clock required")
    now = now.astimezone(UTC)
    day = now.date().isoformat()
    iso = now.isocalendar()
    week = f"{iso.year}-W{iso.week:02d}"
    if previous is None:
        return GuardState(account_fingerprint, day, week, equity, equity, equity)
    if previous.account_fingerprint != account_fingerprint:
        raise ValueError("Account changed: refusing to reuse guard state")
    for number in (
        previous.day_start_equity,
        previous.week_start_equity,
        previous.week_peak_equity,
    ):
        _equity(number)
    if previous.day > day or previous.week > week:
        raise ValueError("Clock moved backwards")
    new_week = previous.week != week
    new_day = previous.day != day
    return GuardState(
        account_fingerprint=account_fingerprint,
        day=day,
        week=week,
        day_start_equity=equity if new_day else previous.day_start_equity,
        week_start_equity=equity if new_week else previous.week_start_equity,
        week_peak_equity=equity if new_week else max(previous.week_peak_equity, equity),
        day_locked=False if new_day else previous.day_locked,
        week_locked=False if new_week else previous.week_locked,
    )


def evaluate_guards(
    state: GuardState,
    *,
    equity: Decimal,
    spread_points: Decimal,
    open_positions: int,
    now: datetime,
    broker_eligible: bool,
    settings: GuardSettings | None = None,
    policy: TradingPolicy | None = None,
) -> GuardResult:
    settings = settings or GuardSettings()
    policy = policy or TradingPolicy()
    _equity(equity)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Timezone-aware clock required")
    if not isinstance(spread_points, Decimal) or not spread_points.is_finite():
        raise ValueError("Missing/invalid spread")
    if type(open_positions) is not int or open_positions < 0:
        raise ValueError("Unknown open positions")
    for base in (state.day_start_equity, state.week_start_equity, state.week_peak_equity):
        _equity(base)

    day_pnl_pct = (equity - state.day_start_equity) * 100 / state.day_start_equity
    day_loss = max(Decimal("0"), state.day_start_equity - equity)
    week_loss = max(Decimal("0"), state.week_start_equity - equity)
    drawdown = max(Decimal("0"), (state.week_peak_equity - equity) * 100
                   / state.week_peak_equity)
    day_limit = state.day_start_equity * policy.max_daily_loss_pct / 100
    week_limit = state.week_start_equity * policy.max_weekly_loss_pct / 100

    day_breached = (
        day_loss >= day_limit
        or (settings.daily_profit_target_pct > 0
            and day_pnl_pct >= settings.daily_profit_target_pct)
    )
    week_breached = (
        week_loss >= week_limit or drawdown >= settings.max_weekly_drawdown_pct
    )
    updated = replace(
        state,
        day_locked=state.day_locked or day_breached,
        week_locked=state.week_locked or week_breached,
    )
    reasons = []
    if not broker_eligible:
        reasons.append("BROKER_INELIGIBLE")
    if spread_points < 0 or spread_points > settings.max_spread_points:
        reasons.append("SPREAD_FILTER")
    if open_positions >= policy.max_open_positions:
        reasons.append("POSITION_LIMIT")
    utc = now.astimezone(UTC)
    if utc.weekday() >= 5 or (utc.weekday() == 4
                              and utc.hour >= settings.friday_lock_hour_utc):
        reasons.append("WEEKEND_LOCK")
    if updated.day_locked:
        reasons.append("DAY_TARGET_OR_LOSS_LOCK")
    if updated.week_locked:
        reasons.append("WEEK_LOSS_OR_DRAWDOWN_LOCK")
    return GuardResult(
        not reasons, tuple(reasons), updated, day_pnl_pct,
        week_loss, day_loss, drawdown,
    )
