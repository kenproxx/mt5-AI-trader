import pytest

from app.ml.dataset import align_training_rows
from app.ml.features import feature_rows
from app.ml.labels import forward_direction_labels


def candles(n=35):
    return [
        {"time": i * 60, "open": 100 + i, "high": 101 + i,
         "low": 99 + i, "close": 100 + i}
        for i in range(n)
    ]


def test_features_causal():
    original = feature_rows(candles(25), lookback=5)
    changed = candles(25)
    changed[-1]["close"] = 10000
    updated = feature_rows(changed, lookback=5)
    assert original == updated


def test_future_label():
    labels = forward_direction_labels(candles(), horizon=3)
    assert labels[0]["label_available_at"] > labels[0]["time"]
    assert labels[0]["target_up"] == 1


def test_dataset_alignment():
    rows = align_training_rows(
        feature_rows(candles(), lookback=5),
        forward_direction_labels(candles(), horizon=3),
    )
    assert len(rows) == 27
    assert all(x["asof_time"] < x["time"] < x["label_available_at"] for x in rows)


def test_duplicate_rejected():
    data = candles()
    data[2]["time"] = data[1]["time"]
    with pytest.raises(ValueError):
        feature_rows(data)


def test_no_lookahead():
    with pytest.raises(ValueError):
        align_training_rows(
            [{"time": 100, "asof_time": 100}],
            [{"time": 100, "label_available_at": 200, "target_up": 1}],
        )
