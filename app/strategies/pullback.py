"""Baseline paper-only EMA pullback signal, no performance claims."""
from dataclasses import dataclass

from app.indicators.trend import ema


@dataclass(frozen=True)
class Signal:
    side: str
    reason: str


def signal_from_closed_candles(m1, m5, m15, h1):
    if any(len(series) < 201 for series in (m1, m5, m15, h1)):
        return Signal("HOLD", "Insufficient warmup")
    close1 = [float(x["close"]) for x in m1]
    close5 = [float(x["close"]) for x in m5]
    close15 = [float(x["close"]) for x in m15]
    closeh = [float(x["close"]) for x in h1]
    e9, e21 = ema(close1, 9)[-1], ema(close1, 21)[-1]
    m5_21 = ema(close5, 21)[-1]
    m15_50 = ema(close15, 50)[-1]
    h1_200 = ema(closeh, 200)[-1]
    if closeh[-1] > h1_200 and close15[-1] > m15_50 and close5[-1] > m5_21 and e9 > e21:
        return Signal("BUY", "Multi-timeframe bullish alignment")
    if closeh[-1] < h1_200 and close15[-1] < m15_50 and close5[-1] < m5_21 and e9 < e21:
        return Signal("SELL", "Multi-timeframe bearish alignment")
    return Signal("HOLD", "No alignment")
