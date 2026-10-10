"""Fail-closed MT5 broker compatibility inspection."""
from datetime import UTC, datetime

from app.broker.models import BrokerState, Validation
from app.config.policy import TradingPolicy


class CompatibilityChecker:
    def __init__(self, adapter, policy=None):
        self.adapter = adapter
        self.policy = policy or TradingPolicy()

    def inspect(self, now_epoch=None, max_tick_age=30):
        try:
            if not self.adapter.initialize() or self.adapter.terminal_info() is None:
                return Validation(BrokerState.BROKER_DISCONNECTED, "MT5 offline")
            account = self.adapter.account_info()
            if account is None:
                return Validation(BrokerState.BROKER_DISCONNECTED, "Missing account")
            if type(account.account_trade_mode) is not int or account.account_trade_mode != 0:
                return Validation(BrokerState.TRADING_DISABLED, "Account DEMO mode unverified", account=account)
            if account.leverage != self.policy.required_leverage:
                return Validation(BrokerState.LEVERAGE_MISMATCH, "Leverage not 1:50", account=account)
            if account.currency != "USD" or account.equity <= 0 or account.free_margin < 0:
                return Validation(BrokerState.TRADING_DISABLED, "Currency or funds invalid", account=account)
            if not account.trade_allowed or not account.trade_expert:
                return Validation(BrokerState.TRADING_DISABLED, "Account trading disabled", account=account)
            if "XAUUSD" not in self.adapter.symbols_get():
                return Validation(BrokerState.SYMBOL_UNAVAILABLE, "Exact XAUUSD missing", account=account)
            if not self.adapter.symbol_select("XAUUSD"):
                return Validation(BrokerState.SYMBOL_UNAVAILABLE, "Symbol selection failed", account=account)
            symbol = self.adapter.symbol_info("XAUUSD")
            if symbol is None:
                return Validation(BrokerState.SYMBOL_UNAVAILABLE, "Symbol info absent", account=account)
            if (symbol.volume_min <= 0 or symbol.volume_step <= 0
                or symbol.volume_max < symbol.volume_min
                or symbol.trade_contract_size <= 0 or symbol.trade_tick_size <= 0
                or symbol.trade_tick_value <= 0 or symbol.point <= 0
                or symbol.trade_stops_level < 0 or symbol.trade_freeze_level < 0):
                return Validation(BrokerState.INVALID_SYMBOL_SPECIFICATION, "Bad symbol specifications", symbol, account=account)
            if symbol.trade_mode != 4:
                return Validation(BrokerState.TRADING_DISABLED, "Symbol not fully tradable", symbol, account=account)
            tick = self.adapter.symbol_info_tick(symbol.name)
            if tick is None or tick.bid <= 0 or tick.ask <= tick.bid:
                return Validation(BrokerState.STALE_DATA, "Invalid quote", symbol, tick, account)
            now = now_epoch if now_epoch is not None else int(datetime.now(UTC).timestamp())
            if tick.time <= 0 or tick.time > now + 5 or now - tick.time > max_tick_age:
                return Validation(BrokerState.STALE_DATA, "Tick stale or future", symbol, tick, account)
            return Validation(BrokerState.TRADE_ELIGIBLE, "Read-only account/symbol checks passed", symbol, tick, account)
        except (ValueError, TypeError, AttributeError, RuntimeError):
            return Validation(BrokerState.NO_TRADE, "Broker inspection error")
