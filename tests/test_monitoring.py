import pytest

from app.monitoring.events import make_event, serialize_event
from app.monitoring.health import assess_health


def test_healthy_demo():
    assert assess_health(broker_connected=True, data_fresh=True,
                         risk_ready=True, demo_account=True).healthy


def test_fail_closed():
    h = assess_health(broker_connected=False, data_fresh=False,
                      risk_ready=True, demo_account=False)
    assert not h.healthy
    assert "not_demo_account" in h.reasons


def test_event_serialization():
    event = make_event("broker", "blocked", reason="stale", mode="demo")
    assert '"state": "blocked"' in serialize_event(event)


def test_reject_secrets():
    with pytest.raises(ValueError):
        make_event("broker", "ok", api_key="SECRET")


def test_reject_complex_fields():
    with pytest.raises(ValueError):
        make_event("broker", "ok", reason={"unexpected": "object"})
