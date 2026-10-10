# Đợt sửa lỗi dữ liệu và đánh giá mô hình

- Backtest: từ chối vốn ban đầu NaN/Infinity, ghi nhận drawdown >=100% khi equity về 0 hoặc âm. Đây vẫn chỉ là thống kê, không phải tick-level simulation.
- ML: thêm hàm purged chronological split dựa trên thời điểm nhãn tương lai được xác nhận; loại bỏ các hàng train/validation có nhãn chạm ranh giới tập tiếp theo.
- Chẩn đoán Demo: Stop Loss <=0 bị chặn.

Các hạn chế còn lại: đồng bộ closed candles đa khung, mô phỏng khớp lệnh thực tế, kiểm soát bảo mật logging/Telegram, CI integration Windows. Không có lệnh giao dịch.
