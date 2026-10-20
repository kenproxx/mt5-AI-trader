"""Strictly read-only XAUUSD scanner using only closed MT5 bars."""
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from math import isfinite

from app.indicators.trend import atr
from app.strategies.pullback import Signal, signal_from_closed_candles

_FRAMES = {"M1": 60, "M5": 300, "M15": 900, "H1": 3600}
_BAR_FIELDS = ("time", "open", "high", "low", "close")


def read_closed_candles(mt5, symbol: str, timeframe: str, *, now_epoch: int):
    """Exclude the forming candle (position 0); reject stale/unaligned rates."""
    seconds = _FRAMES[timeframe]
    rates = mt5.copy_rates_from_pos(
        symbol, getattr(mt5, "TIMEFRAME_" + timeframe), 1, 220,
    )
    if rates is None or len(rates) < 201:
        raise ValueError("Insufficient closed bars")
    candles = []
    previous = None
    for row in rates:
        try:
            stamp = int(row["time"])
            values = {name: float(row[name]) for name in _BAR_FIELDS[1:]}
        except (TypeError, ValueError, KeyError, IndexError, OverflowError) as exc:
            raise ValueError("Malformed MT5 bar") from exc
        if (stamp <= 0 or stamp % seconds != 0
            or previous is not None and stamp <= previous
            or stamp + seconds > now_epoch
            or not all(isfinite(value) and value > 0 for value in values.values())
            or values["high"] < max(values["open"], values["close"], values["low"])
            or values["low"] > min(values["open"], values["close"], values["high"])):
            raise ValueError("Invalid or unclosed bar")
        previous = stamp
        candles.append({"time": stamp, **values})
    if now_epoch - candles[-1]["time"] > max(seconds * 3, seconds + 120):
        raise ValueError("Stale closed bars")
    return candles


def scan_xauusd(mt5, status, *, now_epoch: int):
    if not status.eligible or status.symbol is None or status.tick is None:
        return Signal("HOLD", "Broker not eligible"), None
    data = {
        tf: read_closed_candles(mt5, "XAUUSD", tf, now_epoch=now_epoch)
        for tf in _FRAMES
    }
    signal = signal_from_closed_candles(
        data["M1"], data["M5"], data["M15"], data["H1"],
    )
    if signal.side == "HOLD":
        return signal, None
    # Exclude new orders when volatility is missing or invalid.
    volatility = atr(data["M5"], 14)[-1]
    if not isfinite(volatility) or volatility <= 0:
        return Signal("HOLD", "ATR unavailable"), None
    sym, tick = status.symbol, status.tick
    distance = max(
        Decimal(str(volatility)) * 2,
        Decimal(sym.trade_stops_level + 2) * sym.point,
    )
    if signal.side == "BUY":
        raw = tick.bid - distance
        rounding = ROUND_FLOOR
    else:
        raw = tick.ask + distance
        rounding = ROUND_CEILING
    stop = (raw / sym.trade_tick_size).to_integral_value(rounding=rounding)
    stop *= sym.trade_tick_size
    if stop <= 0:
        return Signal("HOLD", "Invalid stop"), None
    return signal, stop
