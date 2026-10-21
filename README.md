# MT5 AI Trader — Bot nghiên cứu vàng XAUUSD (chỉ Demo)

Dự án Python kết nối MetaTrader 5 (MT5) để **nghiên cứu, kiểm tra rủi ro, mô phỏng và thử giao dịch Demo có kiểm soát** chiến lược giao dịch vàng XAUUSD trên LiteFinance Classic.

> **Cảnh báo:** Đây **chưa phải bot AI giao dịch tự động hoàn chỉnh**. Module mới `app.basket` hỗ trợ gửi lệnh **Demo** khi bật rõ ràng; các công cụ cũ vẫn chỉ đọc. Không cho phép giao dịch tài khoản thật (Live) và **không bảo đảm lợi nhuận**. Kết quả CI chỉ chứng minh các kiểm thử tự động đã chạy thành công, không chứng minh bot hoạt động an toàn trên broker thật.

## 1. Thông số nền tảng

| Thông số | Giá trị |
| --- | --- |
| Sản phẩm | XAUUSD |
| Broker mục tiêu | LiteFinance, MT5 Classic |
| Số vốn tham chiếu | **5 USD** |
| Đòn bẩy bắt buộc | **1:50** |
| Chế độ | **Demo / nghiên cứu**, không Live |
| Rủi ro mục tiêu mỗi lệnh | 0,5% vốn |
| Rủi ro tối đa mỗi lệnh | 1% vốn |
| Giới hạn lỗ trong ngày / tuần | 2% / 5% |
| Dự trữ ký quỹ tự do tối thiểu | 30% vốn |
| Số vị thế mở tối đa | 1 ở bộ nền tảng; module rổ Demo mặc định 6, tổng 0,06 lot |

**Lưu ý quan trọng với vốn 5 USD:** Nếu khối lượng tối thiểu của broker là 0,01 lot và số tiền ký quỹ hoặc mức lỗ tại Stop Loss vượt ngân sách, chương trình phải từ chối giao dịch (`NO_TRADE`). Không tăng đòn bẩy hoặc bỏ qua giới hạn rủi ro để ép mở lệnh. Thông số hợp đồng, spread, bước lot và yêu cầu ký quỹ phải lấy trực tiếp từ MT5, không coi giá trị mô phỏng là số liệu thực tế.

## 2. Cài đặt trên Windows 11

Cài Python 3.11 hoặc 3.12 (64-bit) và MetaTrader 5. Đăng nhập tài khoản **LiteFinance Demo**, tự kiểm tra đúng máy chủ và đòn bẩy 1:50.

Mở PowerShell tại thư mục dự án:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev,mt5]"
python -m pytest -q
ruff check .
python -m app.main --mock
```

Chạy kiểm tra broker thực tế **chỉ đọc**:

```powershell
python -m app.main --real
```

**Cảnh báo:** Lệnh `--real` chỉ kiểm tra broker/rủi ro trên tài khoản Demo qua `CompatibilityChecker` và không cấp quyền gửi lệnh. Dữ liệu phải được xác minh lại trên MT5 thực.

## 3. Kiểm tra tài khoản Demo và ký quỹ

```powershell
python -m scripts.demo_diagnostic --side BUY --stop 2999.00 --costs-usd 0
```

Giá `2999.00` **chỉ là ví dụ**. Phải chọn Stop Loss phù hợp với Bid/Ask hiện tại, bước giá và khoảng cách tối thiểu broker cho phép. Chương trình xác minh `ACCOUNT_TRADE_MODE_DEMO` trước khi tính margin và mức lỗ ước tính. Không gửi lệnh mua/bán.

Có thể lưu bản tóm tắt kiểm tra dạng JSON:

```powershell
python -m scripts.demo_diagnostic --side BUY --stop 2999.00 --audit-json demo-audit.json
```

File mới được tạo mà **không ghi đè file cũ**, chỉ chứa dữ liệu kiểm tra đã giới hạn; trường `can_trade` luôn là `false`. Không chia sẻ dữ liệu tài khoản hoặc báo cáo riêng tư công khai.

## 4. Tiến độ phát triển

| Phase | Chức năng đã có ở mức nền tảng |
| --- | --- |
| 1 | Adapter MT5, kiểm tra broker, quản lý rủi ro, dữ liệu giả lập |
| 2 | Thu thập và xác thực nến OHLC đa khung thời gian |
| 3 | Chỉ báo EMA/ATR, tín hiệu xu hướng và mô phỏng trên giấy |
| 4 | Chỉ số backtest cơ bản, chia tập theo thời gian |
| 5 | Đặc trưng và nhãn dữ liệu phục vụ nghiên cứu ML |
| 6 | Sự kiện giám sát, đánh giá sức khỏe hệ thống |
| 7 | Báo cáo HTML offline, ảnh chụp trạng thái |
| 8 | Gửi cảnh báo Telegram khi bật thủ công, giới hạn tần suất |
| 9 | Danh sách điều kiện đánh giá sẵn sàng Demo |
| 10 | Ước tính tính khả thi của lot tối thiểu |
| 11 | Công cụ chẩn đoán MT5 qua dòng lệnh |
| 12 | Kiểm tra tài khoản Demo dựa trên chế độ MT5 |
| 13 | Bắt buộc xác minh Demo trong công cụ chẩn đoán |
| 14 | Tóm tắt chẩn đoán đã lọc dữ liệu nhạy cảm |
| 15 | Xuất JSON báo cáo chỉ đọc, không ghi đè |

| 16 | Xác minh cấu trúc báo cáo JSON và mã kiểm tra SHA-256 |

Phase 16 đã được merge vào `main`. SHA-256 chỉ hỗ trợ kiểm tra tính toàn vẹn khi có mã đối chiếu đáng tin cậy.

## 5. Cấu trúc thư mục

- `app/basket/`: quản lý rổ Hedge/DCA/Pyramiding/Trim, preview và gửi lệnh Demo bật riêng.
- `app/broker/`: đọc thông tin tài khoản, symbol, báo giá và phép tính MT5.
- `app/risk/`: ước tính khối lượng và các giới hạn rủi ro.
- `app/market_data/`: thu thập, kiểm tra và lưu nến.
- `app/indicators/`, `app/strategies/`, `app/execution/`: chỉ báo, tín hiệu và quyết định paper-only.
- `app/backtesting/`, `app/ml/`: công cụ nghiên cứu; chưa phải bộ máy backtest/AI hoàn chỉnh.
- `app/monitoring/`, `app/dashboard/`, `app/notifications/`: giám sát và báo cáo.
- `app/validation/`: xác minh Demo, chẩn đoán, xuất báo cáo.
- `scripts/`: công cụ chạy thủ công.
- `tests/`: kiểm thử chủ yếu sử dụng dữ liệu mô phỏng.
- `docs/`: tài liệu các phase và báo cáo rà soát mã nguồn.

## 6. Các giới hạn cần xử lý trước khi mở rộng

- **Chưa xác minh bằng terminal LiteFinance Demo thật:** GitHub Actions chạy trên Linux với mock, không thể chứng thực tài khoản, điều kiện hợp đồng và báo giá thực.
- **Chưa có mô phỏng khớp lệnh thực tế:** thiếu tick replay, spread biến động, trượt giá, gap và chi phí giao dịch đầy đủ.
- **Chưa có pipeline huấn luyện/đánh giá mô hình AI:** hiện mới có đặc trưng, nhãn và các phép chia tập.
- **Chưa có hệ thống gửi lệnh Demo được chứng nhận an toàn**, cũng không có tính năng gửi lệnh Live.
- **Đã phát hiện các vấn đề cần sửa** trong quá trình rà soát, đặc biệt ở MockAdapter, kiểm tra Demo tại CLI cũ, đồng bộ dữ liệu đa khung và xử lý dữ liệu rủi ro. Xem `docs/code-review-2026-10.md`.

## 7. Kiểm thử và nguyên tắc an toàn

```powershell
ruff check .
python -m pytest -q
bandit -r app -ll
```

Mọi thay đổi phải đi qua CI và review trước khi merge. Không đưa mật khẩu, token, thông tin đăng nhập vào repository. Chỉ sử dụng tài khoản Demo để kiểm tra; nếu không chắc chắn về điều kiện giao dịch, trả về `NO_TRADE`.

Xem thêm `docs/phase9.md` đến `docs/phase15.md` và `docs/code-review-2026-10.md`.

## 8. Windows VPS — bộ giám sát kiểu VTRADE (Demo, chỉ đọc)

Một hệ thống **độc lập, lấy cảm hứng từ các chức năng quản lý rủi ro và dashboard** của bot giao dịch tự động đã được bổ sung trên nhánh nâng cấp:

- Bộ lọc spread, phiên thứ Sáu/cuối tuần, vị thế mở, giới hạn lỗ/equity drawdown và mục tiêu lợi nhuận ngày (tùy chọn).
- Trạng thái khóa được lưu bền vững qua reboot; bảo vệ chống khởi động lại để xóa giới hạn rủi ro.
- Quét nến đã đóng M1/M5/M15/H1, EMA trend và SL ATR tham khảo, kiểm tra khối lượng paper-only.
- Dashboard đọc trạng thái tại localhost, không có lệnh Buy/Sell/Close.

Chạy một chu kỳ với MT5 Demo đang mở:

```powershell
.\.venv\Scripts\python.exe -m app.automation.worker --mode mt5 --once
```

Chạy theo vòng lặp và dashboard:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_vps_monitor.ps1
# Mở terminal PowerShell khác:
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_vps_dashboard.ps1
```

Xem [hướng dẫn chi tiết](docs/vtrade-style-vps.md). **Bộ giám sát ở mục này chỉ đọc**. Module rổ Demo mới ở mục 9 có gateway gửi lệnh riêng; không mở giao dịch Live. Không sử dụng vốn thật để đánh giá khả năng vận hành của phiên bản này.


## 9. Quản lý rổ lệnh theo 5 tính năng trong ảnh VTrade

Đã bổ sung **Hedge nhiều tầng, DCA trước/sau Hedge, Pyramiding, Trim và giới
hạn tổng lot/ký quỹ**. Thuật toán độc lập theo mô tả người dùng, không sao
chép hay xác nhận hiệu quả của sản phẩm VTrade. Mặc định là preview; hỗ trợ
execution chỉ trên MT5 **Demo hedging, USD, 1:50** với login được chỉ định.

```powershell
# Kiểm tra mock: vốn tham chiếu 5 USD dự kiến bị chặn bởi giới hạn rủi ro.
.\.venv\Scripts\python.exe -m app.basket.worker --once

# Đọc MT5 Demo và xem quyết định, không gửi lệnh.
.\.venv\Scripts\python.exe -m app.basket.worker --mode mt5 --config config/basket.example.json --once

# Dashboard cho module rổ (cửa sổ PowerShell khác).
.\.venv\Scripts\python.exe -m app.automation.dashboard --status-file data/basket-status.json
```

Đọc [hướng dẫn đầy đủ và cách bật gửi lệnh Demo](docs/vtrade-basket.md) trước
khi dùng `--execute-demo`. Cấu hình: [basket.example.json](config/basket.example.json).
Dữ liệu trạng thái: `data/basket-state.sqlite3`. **Chưa kiểm thử tích hợp
trên terminal LiteFinance/Windows VPS thật**; CI chỉ dùng terminal giả.
