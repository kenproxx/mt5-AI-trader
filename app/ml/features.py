"""Point-in-time features from fully closed candles only."""
from math import isfinite


def feature_rows(candles, lookback=20):
    if lookback < 2:
        raise ValueError("lookback must be at least two")
    data = list(candles)
    times = [x["time"] for x in data]
    if any(a >= b for a, b in zip(times, times[1:], strict=False)):
        raise ValueError("Candles must have unique ascending timestamps")
    output = []
    for i in range(lookback, len(data)):
        window = data[i - lookback:i]
        closes = [float(c["close"]) for c in window]
        highs = [float(c["high"]) for c in window]
        lows = [float(c["low"]) for c in window]
        if any(not isfinite(v) for v in closes + highs + lows) or closes[0] <= 0:
            raise ValueError("Invalid candle price")
        output.append({
            "time": data[i]["time"],
            "asof_time": window[-1]["time"],
            "return_window": closes[-1] / closes[0] - 1,
            "range_window": (max(highs) - min(lows)) / closes[-1],
            "trend_window": (closes[-1] - sum(closes) / len(closes)) / closes[-1],
        })
    return output
