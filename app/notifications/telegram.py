"""Explicit opt-in Telegram transport with bounded payload and timeouts."""
import json
from urllib import request


def send_telegram(*, token, chat_id, message, enabled=False):
    if not enabled:
        raise RuntimeError("Telegram delivery disabled by default")
    if not token or not chat_id:
        raise ValueError("Telegram credentials missing")
    if not isinstance(message, str) or len(message) > 2000:
        raise ValueError("Message must be text up to 2000 characters")
    payload = json.dumps({"chat_id": chat_id, "text": message}).encode()
    req = request.Request(
        "https://api.telegram.org/bot" + token + "/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=10) as response:
        data = json.load(response)
    if data.get("ok") is not True:
        raise RuntimeError("Telegram API rejected the alert")
    return True
