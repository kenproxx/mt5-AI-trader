"""Strict UTC candle validation; never fill missing market prices."""
from datetime import UTC, datetime
from decimal import Decimal


class DataQualityError(ValueError):
    pass


def validate_candles(records, timeframe_seconds):
    if timeframe_seconds <= 0:
        raise DataQualityError("Invalid timeframe")
    previous = None
    gaps = []
    cleaned = []
    for r in records:
        ts = int(r["time"])
        if ts <= 0 or ts > int(datetime.now(UTC).timestamp()) + 60:
            raise DataQualityError("Invalid timestamp")
        if previous is not None:
            if ts <= previous:
                raise DataQualityError("Unsorted or duplicate candles")
            if (ts - previous) % timeframe_seconds != 0:
                raise DataQualityError("Off-grid candle timestamps")
            if ts - previous > timeframe_seconds:
                gaps.append((previous, ts))
        o, h, low, c = (Decimal(str(r[k])) for k in ("open", "high", "low", "close"))
        if not all(v.is_finite() and v > 0 for v in (o, h, low, c)):
            raise DataQualityError("Invalid OHLC")
        if low > min(o, c) or h < max(o, c) or low > h:
            raise DataQualityError("Inconsistent OHLC")
        if int(r.get("tick_volume", 0)) < 0 or int(r.get("spread", 0)) < 0:
            raise DataQualityError("Invalid volume/spread")
        cleaned.append(dict(r))
        previous = ts
    return cleaned, gaps
