from datetime import UTC, datetime, timedelta

import pytest

from app.notifications.alerts import Alert, AlertThrottler
from app.notifications.telegram import send_telegram


def test_cooldown():
    t = AlertThrottler(60)
    alert = Alert("broker", "critical", "Disconnected")
    now = datetime(2026, 1, 1, tzinfo=UTC)
    assert t.should_send(alert, now)
    assert not t.should_send(alert, now + timedelta(seconds=30))
    assert t.should_send(alert, now + timedelta(seconds=60))


def test_independent_keys():
    t = AlertThrottler()
    now = datetime(2026, 1, 1, tzinfo=UTC)
    assert t.should_send(Alert("broker", "critical", "a"), now)
    assert t.should_send(Alert("data", "warning", "b"), now)


def test_invalid_severity():
    with pytest.raises(ValueError):
        AlertThrottler().should_send(Alert("broker", "secret", "x"))


def test_clock_regression():
    t = AlertThrottler()
    a = Alert("broker", "warning", "x")
    now = datetime(2026, 1, 1, tzinfo=UTC)
    t.should_send(a, now)
    with pytest.raises(ValueError):
        t.should_send(a, now - timedelta(seconds=1))


def test_telegram_disabled():
    with pytest.raises(RuntimeError):
        send_telegram(token="", chat_id="", message="test")
