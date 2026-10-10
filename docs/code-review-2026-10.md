# Rà soát mã nguồn MT5 AI Trader — 09/10/2026

**Phạm vi:** Đọc mã trên nhánh `main` sau Phase 15: broker, risk, paper execution, dữ liệu thị trường, chiến lược, ML, backtesting, monitoring, dashboard, Telegram, validation, CLI và CI. Đồng thời kiểm tra thiết kế Phase 16 trong PR #23. Đây là **static review**, không phải kiểm thử MT5 LiteFinance thực tế.

## Mức P0 — cần sửa trước khi phát triển giao dịch Demo tự động

1. **Thiếu cổng xác minh Demo tại các API dùng chung** (`app/broker/compatibility.py`, `app/main.py`, `app/risk/engine.py`, `app/broker/preflight.py`). Chỉ CLI `scripts/demo_diagnostic.py` đi qua `verify_demo_mode`. `app.main --real` có thể trả về trạng thái `TRADE_ELIGIBLE` cho tài khoản Live nếu các điều kiện khác hợp lệ. Hiện chưa có `order_send`, nhưng trạng thái này có thể bị sử dụng sai khi thêm execution. **Khuyến nghị:** thêm account mode vào snapshot, bắt buộc xác minh Demo ngay tại CompatibilityChecker và mọi preflight; kiểm thử Live/Contest/Unknown.

2. **Thiếu kiểm tra tính hợp lệ của dữ liệu rủi ro** (`app/risk/engine.py`). `size_order` gọi `x.is_finite()` trước khi kiểm tra kiểu; truyền float/None gây lỗi chưa được xử lý. `daily_start_equity`/`weekly_start_equity` không được xác thực là Decimal hữu hạn; giá trị NaN hoặc sai kiểu có thể gây lỗi. **Khuyến nghị:** validate kiểu và `is_finite` của mọi input, fail-closed, kiểm thử fuzz/boundary.

3. **Kết quả kiểm tra lệnh dùng mã thành công cố định** (`app/broker/preflight.py`). So sánh `retcode == 0` chưa chứng minh tương thích với hằng `TRADE_RETCODE_DONE`/mã trả về `order_check` của MT5. **Khuyến nghị:** kiểm tra theo tài liệu và constant runtime, không xem preflight thành quyền gửi lệnh.

## Mức P1 — ưu tiên cao

4. **MockAdapter tính profit sai kiểu** (`app/broker/mock.py`). `(stop - entry)` là Decimal, `lots` được truyền từ risk/feasibility dưới dạng float; phép `Decimal * float` gây `TypeError`. Do đó nhánh kiểm tra margin/loss có thể bị chặn bởi lỗi mock thay vì được mô phỏng đúng. **Khuyến nghị:** chuyển số lượng về `Decimal(str(lots))` hoặc thống nhất kiểu, thêm test mô phỏng BUY/SELL và xác nhận mức lỗ.

5. **Chiến lược đa khung không kiểm tra thời gian nến** (`app/strategies/pullback.py`). Chỉ yêu cầu mỗi khung có >=201 nến, không xác minh thời điểm đóng nến, tính liên tục hoặc đồng bộ M1/M5/M15/H1. Nếu feed chứa nến đang chạy hoặc dữ liệu tương lai, có thể look-ahead. **Khuyến nghị:** bắt buộc mốc thời gian as-of, kiểm tra closed-bar và căn chỉnh thời gian.

6. **ML dataset chưa có purge/embargo theo thời điểm nhãn** (`app/ml/dataset.py`, `app/backtesting/validation.py`). Nhãn tương lai có thể chồng lấn ranh giới train/validation/test; `chronological_split` chỉ tách theo vị trí. **Khuyến nghị:** tách theo `label_available_at` và purge trước ranh giới.

7. **Bộ kiểm tra OHLC chưa xác thực đầy đủ** (`app/market_data/validation.py`). Kiểm tra bước giữa các timestamp nhưng không buộc timestamp đầu tiên nằm trên lưới khung thời gian; không kiểm tra volume/spread hữu hạn hay các trường phụ. **Khuyến nghị:** chuẩn hóa schema, kiểm tra grid và dữ liệu bất thường, có xử lý giờ thị trường.

8. **Thông tin sự kiện có thể chứa bí mật** (`app/monitoring/events.py`). `reason` và `correlation_id` chấp nhận chuỗi tùy ý rồi chỉ cắt độ dài, không thực sự redaction. **Khuyến nghị:** dùng mã lỗi allowlist và redaction có kiểm thử.

9. **Telegram đưa token vào URL request** (`app/notifications/telegram.py`). Đây là yêu cầu của Telegram Bot API nhưng exception/telemetry từ tầng HTTP có nguy cơ lộ token nếu ghi log nguyên bản; thiếu kiểm thử nhánh HTTP thực tế và retry/backoff. **Khuyến nghị:** sanitize exception, test giả lập HTTPS và hạn chế log request path.

10. **Backtest metrics không mô hình hóa khả năng phá sản** (`app/backtesting/metrics.py`). Khi equity <=0, max drawdown không còn được cập nhật; đầu vào `initial_equity` cũng không xác thực hữu hạn và đúng kiểu đầy đủ. **Khuyến nghị:** giới hạn equity, xác định rõ xử lý phá sản và kiểm thử edge cases.

## Mức P2 — cải tiến chất lượng

11. `app/indicators/trend.py`: ATR là trung bình trượt đơn của True Range, không phải Wilder ATR; cần ghi rõ tên hoặc thay thuật toán.
12. `app/dashboard/snapshot.py`: đặt `demo_account=True` theo tham số mode, không dùng xác minh broker; chỉ nên mô tả là báo cáo offline mô phỏng.
13. `app/validation/audit_export.py`: kiểm tra symlink trước khi mở tạo file còn có rủi ro TOCTOU trong thư mục không đáng tin cậy; dùng cơ chế mở file an toàn ở cấp OS nếu dùng trong môi trường chia sẻ.
14. `app/validation/audit_integrity.py` (PR #23): SHA-256 chỉ là checksum, không xác thực nguồn; cần lưu digest ở nơi tin cậy và kiểm tra nội dung chặt chẽ hơn (timestamp, Decimal, state) nếu dùng để lưu trữ dài hạn.
15. `app/validation/demo_feasibility.py`: thiếu kiểm tra `stop > 0`, chưa xét toàn bộ giới hạn lỗ ngày/tuần; kết quả chỉ là chẩn đoán lot tối thiểu, không phải quyền giao dịch.
16. `.github/workflows/ci.yml`: chỉ chạy lint, pytest, Bandit; thiếu coverage threshold, type checking, property tests, dependency audit và integration test trên Windows MT5 Demo.

## Thứ tự sửa đề xuất

1. Chuẩn hóa và xác minh Demo mode tại broker preflight; không trả `TRADE_ELIGIBLE` nếu chưa chứng minh Demo.
2. Sửa MockAdapter, bổ sung kiểm thử tính toán rủi ro và ký quỹ.
3. Bổ sung validation dữ liệu đầu vào, NaN/Infinity, loss baselines và mã retcode.
4. Xây dựng bộ kiểm tra closed candles đa khung, timestamp và kiểm soát look-ahead.
5. Purged walk-forward và tick-level backtesting có chi phí/spread/slippage.
6. Gia cố bảo mật logging, Telegram và kiểm tra CI Windows.

**Kết luận:** Có nền tảng kiểm thử, cơ chế fail-closed ở nhiều module và không có đường gửi lệnh. Tuy nhiên **chưa đạt tiêu chuẩn cho giao dịch Demo tự động**, càng không phù hợp Live. Cần giải quyết P0/P1 và chạy kiểm tra thực tế trên LiteFinance Demo trước khi xem xét bước tiếp theo.
