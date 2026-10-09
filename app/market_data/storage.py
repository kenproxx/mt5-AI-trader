"""Atomic parquet writes and monotonic incremental merge."""
import os
import tempfile
from pathlib import Path

from app.market_data.validation import validate_candles


def write_parquet(records, path, timeframe_seconds):
    import pyarrow as pa
    import pyarrow.parquet as pq

    clean, gaps = validate_candles(records, timeframe_seconds)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".parquet", delete=False) as tmp:
        temp = Path(tmp.name)
    try:
        pq.write_table(pa.Table.from_pylist(clean), temp)
        os.replace(temp, target)
    finally:
        if temp.exists():
            temp.unlink()
    return len(clean), gaps


def incremental_merge(existing, incoming, timeframe_seconds):
    by_time = {int(row["time"]): dict(row) for row in existing}
    for row in incoming:
        ts = int(row["time"])
        if ts in by_time and by_time[ts] != dict(row):
            raise ValueError("Conflicting historical candle revision")
        by_time[ts] = dict(row)
    return validate_candles([by_time[t] for t in sorted(by_time)], timeframe_seconds)
