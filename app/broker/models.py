"""Typed, immutable snapshots: no write-capable trading API here."""
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class BrokerState(StrEnum):
    BROKER_CONNECTED = "BROKER_CONNECTED"
    BROKER_DISCONNECTED = "BROKER_DISCONNECTED"
    LEVERAGE_MISMATCH = "LEVERAGE_MISMATCH"
    SYMBOL_UNAVAILABLE = "SYMBOL_UNAVAILABLE"
    INVALID_SYMBOL_SPECIFICATION = "INVALID_SYMBOL_SPECIFICATION"
    INSUFFICIENT_MARGIN = "INSUFFICIENT_MARGIN"
    LOT_BELOW_MINIMUM = "LOT_BELOW_MINIMUM"
    RISK_LIMIT_EXCEEDED = "RISK_LIMIT_EXCEEDED"
    TRADING_DISABLED = "TRADING_DISABLED"
    TRADE_ELIGIBLE = "TRADE_ELIGIBLE"
    STALE_DATA = "STALE_DATA"
    ORDER_REJECTED = "ORDER_REJECTED"
    NO_TRADE = "NO_TRADE"


@dataclass(frozen=True)
class AccountSnapshot:
    leverage: int
    currency: str
    equity: Decimal
    free_margin: Decimal
    balance: Decimal
    margin: Decimal
    trade_allowed: bool
    trade_expert: bool
    server: str
    margin_so_call: Decimal = Decimal("0")
    margin_so_so: Decimal = Decimal("0")
    account_trade_mode: int | None = None


@dataclass(frozen=True)
class SymbolSnapshot:
    name: str
    trade_mode: int
    volume_min: Decimal
    volume_max: Decimal
    volume_step: Decimal
    trade_contract_size: Decimal
    trade_tick_size: Decimal
    trade_tick_value: Decimal
    trade_stops_level: int
    trade_freeze_level: int
    trade_exemode: int
    filling_mode: int
    point: Decimal
    digits: int
    visible: bool


@dataclass(frozen=True)
class TickSnapshot:
    bid: Decimal
    ask: Decimal
    time: int


@dataclass(frozen=True)
class Validation:
    state: BrokerState
    reason: str
    symbol: SymbolSnapshot | None = None
    tick: TickSnapshot | None = None
    account: AccountSnapshot | None = None

    @property
    def eligible(self) -> bool:
        return self.state == BrokerState.TRADE_ELIGIBLE
