import pytest

from app.monitoring.events import make_event, serialize_event
from app.monitoring.health import assess_health


def test_health_does_not_require_account_type():
    assert assess_health(broker_connected=True, data_fresh=True,
                         risk_ready=True).healthy


def test_fail_closed():
    h = assess_health(broker_connected=False, data_fresh=False,
                      risk_ready=True)
    assert not h.healthy
    assert h.reasons == ("broker_disconnected", "market_data_stale")


def test_event_serialization():
    event = make_event("broker", "blocked", reason="stale", mode="demo")
    assert '"state": "blocked"' in serialize_event(event)


def test_reject_secrets():
    with pytest.raises(ValueError):
        make_event("broker", "ok", api_key="SECRET")


def test_reject_complex_fields():
    with pytest.raises(ValueError):
        make_event("broker", "ok", reason={"unexpected": "object"})
