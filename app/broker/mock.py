"""Synthetic test-only adapter; never represents real LiteFinance trading terms."""
from decimal import Decimal
from time import time

from app.broker.models import AccountSnapshot, SymbolSnapshot, TickSnapshot


class MockAdapter:
    def __init__(self):
        self.connected = True
        self.account = AccountSnapshot(50, "USD", Decimal("5"), Decimal("5"), Decimal("5"),
                                       Decimal("0"), True, True, "MOCK", account_trade_mode=0)
        self.symbol = SymbolSnapshot("XAUUSD", 4, Decimal("0.01"), Decimal("10"),
                                     Decimal("0.01"), Decimal("100"), Decimal("0.01"),
                                     Decimal("1"), 10, 0, 2, 1, Decimal("0.01"), 2, True)
        self.tick = TickSnapshot(Decimal("3000.00"), Decimal("3000.20"), int(time()))
        self.order_check_result = type("Check", (), {"retcode": 10009})()

    def initialize(self):
        return self.connected

    def shutdown(self):
        pass

    def terminal_info(self):
        return object() if self.connected else None

    def account_info(self):
        return self.account

    def symbols_get(self):
        return ["XAUUSD"]

    def symbol_select(self, name):
        return name == "XAUUSD"

    def symbol_info(self, name):
        return self.symbol if name == "XAUUSD" else None

    def symbol_info_tick(self, name):
        return self.tick if name == "XAUUSD" else None

    def order_calc_profit(self, side, symbol, lots, entry, stop):
        if side == "BUY":
            return (Decimal(str(stop)) - Decimal(str(entry))) * Decimal(str(lots)) * self.symbol.trade_contract_size
        return (Decimal(str(entry)) - Decimal(str(stop))) * Decimal(str(lots)) * self.symbol.trade_contract_size

    def order_calc_margin(self, side, symbol, lots, price):
        return Decimal(str(price)) * Decimal(str(lots)) * self.symbol.trade_contract_size / 50

    def order_check(self, request):
        return self.order_check_result
