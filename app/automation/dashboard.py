"""Local-only HTML status dashboard. No control, trading, or remote bind."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PAGE = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MT5 XAUUSD — DEMO Watch</title>
<style>
:root{font-family:system-ui,Arial,sans-serif;color-scheme:dark;
background:#0c1524;color:#e5eaf3}
body{margin:0;padding:32px;max-width:1050px;margin-inline:auto}
header{display:flex;align-items:center;justify-content:space-between;gap:16px}
h1{font-size:24px;margin:0 0 6px}p{color:#a8b7cb;margin:0}
.tag{border:1px solid #4c6688;border-radius:50px;padding:8px 12px;font-size:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin:28px 0}
.card{background:#15253a;border:1px solid #2c3e57;border-radius:16px;padding:20px}
.card small{display:block;color:#9cb0ca;margin-bottom:14px}
.value{font-size:25px;font-weight:700;overflow-wrap:anywhere}
.safe{color:#73deb4}.warn{color:#f2ba74}
aside{color:#92a5be;font-size:13px;margin-top:20px;line-height:1.6}
</style></head>
<body>
<header><div><h1>MT5 XAUUSD Control Center</h1>
<p>Windows VPS · Dashboard chỉ đọc · Xem chế độ worker bên dưới</p></div>
<div class="tag" id="health">Đang đọc...</div></header>
<section class="grid" id="cards"></section>
<div class="card"><small>Điều kiện chặn lệnh mới</small>
<div class="value warn" id="blockers">Đang đọc...</div></div>
<aside>Không có chức năng Buy/Sell/Close. Các chỉ số dựa trên equity của MT5,
không phải báo cáo lợi nhuận đã thực hiện. Không mở cổng này ra Internet.<br>
Cập nhật từ dữ liệu giám sát mỗi 10 giây. Giới hạn spread và loss có thể
khiến bot ở trạng thái NO_TRADE, kể cả khi có tín hiệu.</aside>
<script>
const labels=[
["timestamp_utc","Cập nhật UTC"],["mode","Chế độ worker"],["broker_state","MT5 / Broker"],
["equity_usd","Equity (USD)"],["spread_points","Spread (points)"],
["day_equity_change_pct","Thay đổi equity ngày (%)"],
["week_drawdown_pct","Drawdown tuần (%)"],["open_positions","Vị thế đang mở"],
["signal","Tín hiệu nghiên cứu"],["paper_lots","Lot quyết định"],
["paper_stop","Stop Loss quyết định"],
["basket_phase","Trạng thái rổ"],["total_lots","Tổng lot (gross)"],
["basket_pnl_usd","PnL nổi của rổ (USD)"],["layers","Số tầng đã mở"],
["action","Quyết định"],["execution","Kết quả thực thi"]
];
async function update(){
  try {
    const r=await fetch('/api/status',{cache:'no-store'});
    if(!r.ok) throw Error('No data');
    const data=await r.json();
    const grid=document.getElementById('cards');
    grid.replaceChildren();
    for(const [key,label] of labels){
       const card=document.createElement('div');card.className='card';
       const small=document.createElement('small');small.textContent=label;
       const value=document.createElement('div');value.className='value';
       value.textContent=String(data[key]??'—');
       card.append(small,value);grid.append(card);
    }
    const age=Date.now()-Date.parse(data.timestamp_utc??'');
    const stale=!Number.isFinite(age)||age>90000||age < -5000;
    document.getElementById('health').textContent=stale?'DỮ LIỆU CŨ / WORKER DỪNG':
      String(data.mode??'DEMO_READ_ONLY')+' · '+String(data.execution??'READ ONLY');
    document.getElementById('blockers').textContent=
      (data.blockers??[]).join(' · ')||'Không có chặn bổ sung';
  } catch(_){
    document.getElementById('health').textContent='DỮ LIỆU KHÔNG KHẢ DỤNG';
    document.getElementById('blockers').textContent='Không đọc được báo cáo.';
  }
}
update();setInterval(update,10000);
</script></body></html>"""


def make_handler(status_file):
    path = Path(status_file)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                body, kind, code = PAGE.encode("utf-8"), "text/html; charset=utf-8", 200
            elif self.path == "/api/status":
                try:
                    report = json.loads(path.read_text(encoding="utf-8"))
                    body = json.dumps(report, ensure_ascii=False).encode("utf-8")
                    code = 200
                except (OSError, ValueError):
                    body, code = b'{"blockers":["STATUS_UNAVAILABLE"]}', 503
                kind = "application/json; charset=utf-8"
            else:
                body, kind, code = b"Not found", "text/plain", 404
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy",
                             "default-src 'none'; style-src 'unsafe-inline'; "
                             "script-src 'unsafe-inline'; connect-src 'self'")
            self.end_headers()
            self.wfile.write(body)

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--status-file", default="data/vps-status.json")
    args = parser.parse_args()
    if not (1024 <= args.port <= 65535):
        parser.error("Port must be between 1024 and 65535")
    server = ThreadingHTTPServer(
        ("127.0.0.1", args.port), make_handler(args.status_file)
    )
    print(f"Local read-only dashboard: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
