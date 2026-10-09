"""Causal indicators: completed candles only."""


def ema(values, period):
    if period <= 0:
        raise ValueError("period must be positive")
    result = []
    alpha = 2 / (period + 1)
    current = None
    for value in values:
        value = float(value)
        current = value if current is None else alpha * value + (1 - alpha) * current
        result.append(current)
    return result


def atr(candles, period=14):
    if period <= 0:
        raise ValueError("period must be positive")
    ranges = []
    previous_close = None
    for candle in candles:
        high, low, close = (float(candle[k]) for k in ("high", "low", "close"))
        ranges.append(max(high - low, abs(high - previous_close), abs(low - previous_close))
                      if previous_close is not None else high - low)
        previous_close = close
    result = []
    for index in range(len(ranges)):
        window = ranges[max(0, index - period + 1):index + 1]
        result.append(sum(window) / len(window))
    return result
