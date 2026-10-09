"""Generate a static offline HTML report without exposing secrets."""
from dataclasses import asdict
from html import escape


def render_html(snapshot):
    values = asdict(snapshot)
    rows = "".join(
        "<tr><th scope='row'>" + escape(str(key)) + "</th><td>" +
        escape(", ".join(value) if isinstance(value, tuple) else str(value)) +
        "</td></tr>"
        for key, value in values.items()
    )
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>MT5 Demo Monitoring</title>"
        "<style>body{font:16px system-ui;max-width:800px;margin:3rem auto;"
        "padding:1rem}table{border-collapse:collapse;width:100%}"
        "td,th{border:1px solid #aaa;padding:.75rem;text-align:left}</style>"
        "</head><body><h1>MT5 Demo Monitoring</h1>"
        "<p>Offline read-only report. Not a trading control panel.</p>"
        "<table>" + rows + "</table></body></html>"
    )
