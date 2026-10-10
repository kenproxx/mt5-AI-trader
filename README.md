# MT5 AI Trader — Bot nghiên cứu vàng XAUUSD (chỉ Demo)

Dự án Python kết nối MetaTrader 5 (MT5) để **nghiên cứu, kiểm tra rủi ro và mô phỏng** chiến lược giao dịch vàng XAUUSD trên LiteFinance Classic.

> **Cảnh báo:** Đây **chưa phải bot AI giao dịch tự động hoàn chỉnh**. Mã nguồn hiện không triển khai `order_send`, không cho phép giao dịch tài khoản thật (Live) và **không bảo đảm lợi nhuận**. Kết quả CI chỉ chứng minh các kiểm thử tự động đã chạy thành công, không chứng minh bot hoạt động an toàn trên broker thật.

## 1. Thông số cố định

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
| Số vị thế mở tối đa | 1 |

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

**Cảnh báo:** Lệnh `--real` hiện chỉ kiểm tra khả năng tương thích và rủi ro; chưa tự xác minh `trade_mode` của tài khoản là Demo. Không dùng đầu ra của lệnh này để cấp phép giao dịch.

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

## Cải tiến từ báo cáo review

Đã bổ sung kiểm tra tài khoản Demo tại broker, chuẩn hóa đầu vào rủi ro, sửa MockAdapter và retcode preflight. Đợt tiếp theo bổ sung chia tập ML theo thời gian có loại bỏ nhãn chồng lấn và xử lý drawdown khi vốn về 0. Xem `docs/code-review-2026-10.md` và `docs/review-fixes-phase2.md`. Các cải tiến chưa chứng minh bot giao dịch được trên LiteFinance Demo thật.
