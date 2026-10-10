from decimal import Decimal

import pytest

from app.backtesting.metrics import summarize
from app.ml.purged_split import purged_chronological_split


def test_backtest_bankruptcy_drawdown():
    result = summarize([Decimal("-6")])
    assert result["max_drawdown_pct"] >= Decimal("100")


@pytest.mark.parametrize("invalid", [Decimal("NaN"), Decimal("Infinity"), Decimal("0")])
def test_backtest_invalid_initial_equity(invalid):
    with pytest.raises(ValueError):
        summarize([Decimal("1")], initial_equity=invalid)


def test_purged_split_drops_leaking_labels():
    rows = [
        {"time": i, "asof_time": i - 1, "label_available_at": i + 3}
        for i in range(40)
    ]
    train, validation, test = purged_chronological_split(rows)
    assert max(x["label_available_at"] for x in train) < validation[0]["time"]
    assert max(x["label_available_at"] for x in validation) < test[0]["time"]
    assert len(train) < 24


def test_purged_split_rejects_bad_timestamps():
    rows = [
        {"time": i, "asof_time": i, "label_available_at": i + 1}
        for i in range(30)
    ]
    with pytest.raises(ValueError):
        purged_chronological_split(rows)
