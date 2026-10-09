"""Pure alert throttling logic; no network side effects."""
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True)
class Alert:
    key: str
    severity: str
    message: str


class AlertThrottler:
    def __init__(self, cooldown_seconds=300):
        if cooldown_seconds < 0:
            raise ValueError("cooldown must be nonnegative")
        self.cooldown = timedelta(seconds=cooldown_seconds)
        self._last_sent = {}

    def should_send(self, alert, now=None):
        if alert.severity not in {"info", "warning", "critical"}:
            raise ValueError("Unsupported severity")
        if not alert.key or len(alert.key) > 100:
            raise ValueError("Invalid alert key")
        now = now or datetime.now(UTC)
        if now.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware")
        previous = self._last_sent.get(alert.key)
        if previous is not None and now < previous:
            raise ValueError("Clock moved backwards")
        if previous is not None and now - previous < self.cooldown:
            return False
        self._last_sent[alert.key] = now
        return True
