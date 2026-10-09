"""Explicit opt-in Telegram transport with bounded payload and timeouts."""
import http.client
import json


def send_telegram(*, token, chat_id, message, enabled=False):
    if not enabled:
        raise RuntimeError("Telegram delivery disabled by default")
    if not token or not chat_id:
        raise ValueError("Telegram credentials missing")
    if not isinstance(message, str) or len(message) > 2000:
        raise ValueError("Message must be text up to 2000 characters")
    payload = json.dumps({"chat_id": chat_id, "text": message}).encode()
    conn = http.client.HTTPSConnection("api.telegram.org", timeout=10)
    try:
        conn.request(
            "POST", "/bot" + token + "/sendMessage",
            body=payload, headers={"Content-Type": "application/json"},
        )
        response = conn.getresponse()
        data = json.loads(response.read(65536))
        if response.status != 200 or data.get("ok") is not True:
            raise RuntimeError("Telegram API rejected the alert")
    finally:
        conn.close()
    return True
