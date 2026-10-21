# Bộ điều khiển XAUUSD kiểu VTrade — phiên bản thử nghiệm (độc lập)

Tài liệu này mô tả riêng worker giám sát cũ. Bộ quản lý rổ mới hỗ trợ 5 tính năng trong ảnh và gửi lệnh Demo bật riêng: [xem hướng dẫn](vtrade-basket.md).

Bộ tính năng này **không phải mã nguồn VTRADE**, không bảo đảm giống chính xác sản phẩm thương mại hoặc có lợi nhuận. Một số sản phẩm tên VTrade là copy-trading, một số là MT5 EA; không đồng nhất.

## Đã triển khai
- Chạy tiến trình quan sát MT5 trên **Windows VPS**, chỉ DEMO và chỉ đọc.
- Kiểm tra tài khoản USD, 1:50, XAUUSD, giá hợp lệ qua CompatibilityChecker hiện có.
- Lấy **nến đóng** M1, M5, M15, H1 (bỏ nến đang hình thành); xác minh timestamp, độ mới, OHLC hợp lệ.
- Tạo tín hiệu EMA nhiều khung đã có sẵn; SL tham khảo từ 2×ATR(M5), tôn trọng tick-size/minimum stop.
- Tính lot bằng RiskEngine hiện có. **Không đặt lệnh**, không giả định có thể khớp lệnh.
- Chặn khi spread cao, đã có một vị thế, quá giới hạn lỗ ngày/tuần, drawdown tuần, thứ Sáu từ 20:00 UTC và cuối tuần.
- Khóa lệnh mới theo biến động **equity** so với đầu ngày, đầu tuần; tự gài chốt và lưu JSON trong data/ qua lần restart. Mục tiêu lợi nhuận ngày mặc định **tắt**, chỉ bật thủ công.
- Dashboard cục bộ tại `http://127.0.0.1:8765`: equity, spread, drawdown, vị thế, tín hiệu, trạng thái chặn. Không có Buy/Sell/Close.

## Cài đặt VPS
Dùng Windows Server 2022/2025, Python 3.12 64-bit, Git, MT5 LiteFinance chạy trong **phiên người dùng đăng nhập**.

```powershell
git clone https://github.com/kenproxx/mt5-AI-trader.git
cd mt5-AI-trader
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,mt5]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m app.automation.worker --mode mock --once
```

Đăng nhập MT5 **Demo** (LiteFinance Classic, USD, 1:50), mở biểu đồ XAUUSD và xác minh contract/lot/spread trong terminal. Không cấp quyền cho Python gửi lệnh nếu chỉ dùng bộ quan sát.

```powershell
# 1 chu kỳ: đọc terminal thật nhưng KHÔNG gửi lệnh
.\.venv\Scripts\python.exe -m app.automation.worker --mode mt5 --once

# Chạy liên tục
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_vps_monitor.ps1
```

Mở PowerShell khác:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_vps_dashboard.ps1
```

Từ trình duyệt **trong VPS**: `http://127.0.0.1:8765`

Có thể dùng Task Scheduler tạo **hai task**, cùng Trigger *At log on*, Action `powershell.exe`, arguments là `-NoProfile -ExecutionPolicy Bypass -File "C:\Bots\mt5-AI-trader\scripts\run_vps_monitor.ps1"` và tương tự với `run_vps_dashboard.ps1`. Thiết lập chạy khi user đã đăng nhập, không khởi chạy thêm phiên bản nếu task còn chạy, khởi chạy lại khi lỗi. Không công bố port 8765 ra Internet. RDP Disconnect (không Sign out) khi cần duy trì phiên MT5.

## Các giá trị có thể tùy chỉnh
```powershell
.\.venv\Scripts\python.exe -m app.automation.worker --mode mt5 --once --max-spread-points 50 --daily-target-pct 1 --estimated-costs-usd 0.01
```

- `--daily-target-pct 0` (mặc định): tắt mục tiêu lợi nhuận ngày.
- `--daily-target-pct 1`: gài khóa tín hiệu mới khi equity tăng tối thiểu 1% so với đầu ngày; **không đóng vị thế**.
- `--max-spread-points 50` có đơn vị là **MT5 point**, không phải USD. Phải chỉnh theo dữ liệu symbol thực.
- `--estimated-costs-usd`: số tiền dự trù thủ công cho phí trong mô phỏng, không thay thế kiểm chứng commission/slippage từ broker.

## Giới hạn và lưu ý trước khi xem xét Demo auto-trade
1. Chưa có `order_send`, sửa SL/TP, trailing stop thực tế, thoát lệnh tự động, news calendar thực, hoặc copy-trading. Dashboard chỉ đọc và không phải PnL đã thực hiện.
2. Rủi ro đo từ equity nên nạp/rút tiền, swap, hoặc biến động vị thế đang mở có thể làm sai baseline. Muốn triển khai gửi lệnh cần tính chính xác realized PnL từ `history_deals_get`, phát hiện cashflow, chi phí và đối chiếu trạng thái sau reconnect.
3. Bot chưa được kiểm thử với Windows VPS và tài khoản LiteFinance thực: CI trên Linux chỉ dùng mock. Cần kiểm thử Windows/MT5 Demo và thêm kiểm thử tích hợp trước khi bật execution.
4. File `data/vps-guard-state.json` chứa baseline/khóa tài khoản theo hash login+server. **Không xóa file để vượt giới hạn**. Khi thay tài khoản, worker chặn bằng `WORKER_ERROR`; phải đánh giá và khởi tạo môi trường/state mới có kiểm soát.
5. Khoản vốn 5 USD, tài khoản đòn bẩy 1:50 thường không cho phép giao dịch 0.01 lot XAUUSD trong các giới hạn rủi ro đã định; khi broker từ chối lot tối thiểu cần giữ `NO_TRADE`, tuyệt đối không nới giới hạn cho đủ lệnh.
6. Trong mọi trường hợp **không có cơ chế tự bật Live**; tuyệt đối không commit mật khẩu MT5, token Telegram hoặc báo cáo riêng tư.

## Kiểm thử
```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\bandit.exe -r app -ll
```

Mức độ hoàn thành: một **bản nâng cấp giám sát và risk-gating thực sự hoạt động khi dữ liệu đầu vào hợp lệ**, chưa phải bot giao dịch tự động tương đương sản phẩm VTRADE thương mại.
