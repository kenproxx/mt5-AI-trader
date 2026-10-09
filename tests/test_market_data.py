from datetime import UTC, datetime

import pytest

from app.market_data.storage import incremental_merge
from app.market_data.validation import DataQualityError, validate_candles


def candle(t):
    return {"time": t, "open": 3000, "high": 3001, "low": 2999,
            "close": 3000, "tick_volume": 20, "spread": 15}


def test_valid():
    a, gaps = validate_candles([candle(1700000040), candle(1700000100)], 60)
    assert len(a) == 2 and not gaps


def test_gap_reported_not_filled():
    a, gaps = validate_candles([candle(1700000040), candle(1700000160)], 60)
    assert len(a) == 2 and len(gaps) == 1


def test_duplicate_rejected():
    with pytest.raises(DataQualityError):
        validate_candles([candle(1700000040)] * 2, 60)


def test_bad_ohlc_rejected():
    a = candle(1700000040)
    a["low"] = 3005
    with pytest.raises(DataQualityError):
        validate_candles([a], 60)


def test_incremental_idempotent():
    a, gaps = incremental_merge([candle(1700000040)], [candle(1700000040)], 60)
    assert len(a) == 1 and not gaps


def test_incremental_revision_rejected():
    a = candle(1700000040)
    b = dict(a, close=3000.5)
    with pytest.raises(ValueError):
        incremental_merge([a], [b], 60)


def test_utc():
    from app.market_data.collector import MarketDataCollector
    assert MarketDataCollector.utc_timestamp(0) == datetime(1970, 1, 1, tzinfo=UTC)
