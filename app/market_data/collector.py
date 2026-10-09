"""Read-only MT5 historical bars; no fabricated data."""
from datetime import UTC, datetime
from app.market_data.validation import validate_candles

TIMEFRAMES = {"M1": 60, "M5": 300, "M15": 900, "H1": 3600}


class MarketDataCollector:
    def __init__(self, mt5):
        self.mt5 = mt5

    def fetch(self, symbol, timeframe, start_utc, end_utc):
        if timeframe not in TIMEFRAMES:
            raise ValueError("Unsupported timeframe")
        if start_utc.tzinfo is None or end_utc.tzinfo is None:
            raise ValueError("UTC-aware datetimes required")
        if start_utc >= end_utc:
            raise ValueError("Invalid range")
        tf = getattr(self.mt5, "TIMEFRAME_" + timeframe)
        rates = self.mt5.copy_rates_range(
            symbol, tf, start_utc.astimezone(UTC), end_utc.astimezone(UTC)
        )
        if rates is None:
            raise RuntimeError("MT5 returned no history")
        records = [{name: row[name].item() if hasattr(row[name], "item") else row[name]
                    for name in row.dtype.names} for row in rates]
        return validate_candles(records, TIMEFRAMES[timeframe])

    @staticmethod
    def utc_timestamp(ts):
        return datetime.fromtimestamp(ts, UTC)
