# Hedge, DCA, Pyramiding và Trim trên Windows VPS

Bản này triển khai độc lập **5 nhóm tính năng trong ảnh bạn cung cấp**.
Ảnh là phần tổng quan do AI tạo, không phải đặc tả của nhà phát triển VTrade;
không thể từ đó xác nhận bot có cùng thuật toán hoặc kết quả giao dịch.

## Tính năng đã có

| Tính năng | Quy tắc thực tế trong mã |
| --- | --- |
| Hedge nhiều tầng | Khi giá đi ngược từ giá vào lệnh đầu tiên đủ số points, mở hướng ngược để đạt tỷ lệ Hedge cấu hình. Trừ khối lượng Hedge đang tồn tại, làm tròn xuống bước lot; không vượt 100% khối lượng hướng chính. |
| DCA trước/sau Hedge | Hai danh sách khoảng cách độc lập; mỗi tầng chỉ mở một lần trong rổ. Dùng lot cố định, không nhân lot sau thua lỗ. Trạng thái “đã Hedge” giữ đến khi hết rổ. |
| Pyramiding | Thêm lệnh cùng hướng khi tất cả lệnh chính đang có lãi sau dự trù phí, tín hiệu đa khung cùng hướng, đủ khoảng cách và chưa Hedge trong rổ này. |
| Trim | Đóng nguyên ticket thắng, kiểm tra lợi nhuận đã thực hiện từ MT5 deal history, rồi đóng nguyên ticket lỗ nếu đủ bù phí và buffer. Bản này chưa tỉa một phần lot. |
| Quản lý vốn | Giới hạn số vị thế, tổng lot cả hai chiều, rủi ro từng lệnh và tất cả SL, free margin, margin level, lỗ ngày/tuần; kiểm tra cả `order_calc_margin` và `order_check`. |

Kèm theo: SL ở broker cho mỗi lệnh mở; mục tiêu lãi rổ tùy chọn; thoát rổ khi
PnL nổi sau dự trù phí lỗ ít nhất 1% balance hoặc chạm khóa lỗ ngày/tuần;
cooldown; lọc spread/giờ mở lệnh; lưu bộ đếm, khóa rủi ro và intent trong
SQLite; dashboard xem trạng thái. Khi thoát rổ, thử kiểm tra các ticket để
tìm lệnh đóng phù hợp ký quỹ, nhưng chỉ gửi **một lệnh đóng mỗi chu kỳ**.
Trim có thể gồm hai lệnh đóng tuần tự, mỗi lệnh đều có kiểm tra riêng.

## Hai chế độ với MT5

- **Preview (mặc định):** đọc MT5 Demo, tính quyết định, cập nhật báo cáo;
  không gọi `order_send`, không giả lập rằng vị thế đã được mở.
- **Demo execution:** chỉ khi có `--execute-demo --account-login SO_TAI_KHOAN`.
  Bot kiểm tra tài khoản Demo, USD, đòn bẩy **1:50**, chế độ **hedging**, cho
  phép lệnh đối ứng, không áp dụng FIFO, và đúng login đã chỉ định. Không
  có tùy chọn Live. Dùng tài khoản Demo riêng cho bot, cùng một Windows user.

Các lệnh cũ `app.main`, `scripts.demo_diagnostic`, `app.automation.worker`
vẫn chỉ đọc. Gateway mới nằm trong `app/basket/gateway.py`.

## Cài đặt và chạy

Trong PowerShell tại VPS Windows có Git, Python 3.11/3.12 64-bit và MT5:

```powershell
git clone https://github.com/kenproxx/mt5-AI-trader.git
cd mt5-AI-trader
git switch feature/vtrade-style-vps-guardrails
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,mt5]"
.\.venv\Scripts\python.exe -m pytest -q
```

Nếu đã clone repo, cập nhật đúng nhánh PR sau khi bảo toàn thay đổi riêng.
PR chưa merge thì `main` chưa có tính năng này.

1. Kiểm tra pipeline với dữ liệu giả, không cần MT5:

```powershell
.\.venv\Scripts\python.exe -m app.basket.worker --once
```

Kết quả dự kiến của ví dụ mặc định 5 USD là `ORDER_RISK_LIMIT`; tín hiệu
BUY ở chế độ mock chỉ là đầu vào tổng hợp để kiểm tra pipeline.

2. Mở MT5, đăng nhập tài khoản **Demo hedging** USD 1:50; chạy một vòng preview:

```powershell
.\.venv\Scripts\python.exe -m app.basket.worker --mode mt5 --config config/basket.example.json --once
```

3. Chạy preview liên tục và xem dashboard trong cửa sổ PowerShell khác:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_vps_basket.ps1
.\.venv\Scripts\python.exe -m app.automation.dashboard --status-file data/basket-status.json
```

Mở `http://127.0.0.1:8765` **trong VPS**. Dashboard chỉ đọc, hiển thị chế độ
worker, quyết định, kết quả thực thi, tổng lot, PnL nổi, số tầng và lý do
chặn. Dữ liệu quá 90 giây được đánh dấu cũ. Chu kỳ mặc định 30 giây; nếu
chỉnh dài hơn 90 giây, dashboard vẫn đánh dấu cũ giữa các lần cập nhật.

4. Chỉ khi chủ động thử **gửi lệnh Demo**, thay số ví dụ bằng login Demo của bạn:

```powershell
.\.venv\Scripts\python.exe -m app.basket.worker --mode mt5 --config config/basket.example.json --account-login 12345678 --execute-demo --once
```

Chạy liên tục qua launcher:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_vps_basket.ps1 -AccountLogin 12345678 -ExecuteDemo
```

Lệnh này có thể mở/đóng vị thế Demo khi tín hiệu và tất cả điều kiện hợp lệ.
Không đưa mật khẩu vào cấu hình; bot dùng phiên MT5 đã đăng nhập. Dừng bằng
Ctrl+C **không đóng các vị thế đang mở**; SL tại broker vẫn còn. Task
Scheduler dùng *At log on*, cùng user chạy MT5, và không tạo thêm phiên bản
nếu task đã chạy. RDP Disconnect để giữ phiên, không Sign out.

## Cấu hình

Sửa `config/basket.example.json` trước lần chạy đầu tiên. Decimal được lưu
bằng chuỗi để tránh làm tròn. Các số dưới đây là giá trị minh họa phần mềm,
**không phải bộ thông số được khuyến nghị hoặc đã backtest**.

| Khóa | Mặc định | Ý nghĩa |
| --- | --- | --- |
| `lot` | 0.01 | Lot cố định của seed/DCA/pyramid; vẫn phải đúng broker step. |
| `max_positions` / `max_total_lots` | 6 / 0.06 | Trần vị thế và gross lot (BUY + SELL). |
| `dca_before_points` | [300] | Khoảng cách adverse từ giá seed trước Hedge. |
| `dca_after_points` | [900, 1500] | Khoảng cách adverse từ giá seed sau Hedge. |
| `hedge_points` / `hedge_ratios` | [600, 1200] / [0.5, 1] | Ngưỡng adverse và tỷ lệ tổng Hedge so với lot hướng chính. |
| `pyramid_step_points` / `max_pyramid_layers` | 300 / 2 | Khoảng thuận chiều từ giá seed cho từng tầng. |
| `stop_points` | 2000 | SL từ Bid khi BUY, từ Ask khi SELL; tôn trọng stop/tick của broker. |
| `trim_enabled` / `trim_buffer_usd` | true / 0.10 | Bật tỉa nguyên ticket và số tiền dư tối thiểu dự kiến. |
| `costs_per_lot_usd` | 10 | Dự trù phí theo lot. Phải đánh giá lại theo broker, swap và slippage. |
| `basket_take_profit_usd` | 0 | 0 = tắt; giá trị dương kích hoạt thoát rổ khi đạt mục tiêu nổi sau dự trù phí. |
| `max_spread_points` | 50 | Trần spread cho lệnh mở; không chặn thoát chỉ vì spread cao. |
| `min_margin_level_pct` | 200 | Trần sử dụng margin quy đổi thành margin level tối thiểu. |
| `cooldown_seconds` | 60 | Khoảng chờ giữa các lệnh mở. |
| `deviation_points` | 20 | Deviation gửi MT5; broker Market Execution có thể không bảo đảm mức trượt này. |
| `magic` | 5202601 | Mã riêng của bot; không dùng chung với EA khác. |

**Point** lấy từ `symbol_info().point`, không mặc định bằng một USD hoặc một pip.
Vị thế đóng bởi SL/Trim không làm giảm bộ đếm tầng; chỉ khi rổ rỗng mới reset.
Mỗi điều kiện đều chịu trần rủi ro; cấu hình 2 tầng Hedge không có nghĩa cả
hai luôn được phép mở. Nếu Hedge sau làm tròn dưới lot tối thiểu, bot giữ
nguyên và báo `HEDGE_BELOW_MINIMUM`, không tự nâng lot.

Giới hạn cố định của module mới: lệnh mở tối đa 0,5% equity, tổng phần lỗ
còn lại tới các SL tối đa 1% equity và không vượt phần ngân sách lỗ ngày/tuần
còn lại; lỗ ngày 2%, tuần 5%; dự trữ free margin ít nhất 30%. Các mốc ngày/tuần
là UTC. Hedge không được dùng để trừ risk hoặc gross lot. Vốn **5 USD** không
được tự nâng lên và đòn bẩy không được nới để ép mở lệnh; hệ thống có thể
luôn trả `NO_TRADE` ở mức vốn này.

## Khởi động lại và xử lý lỗi

- Dùng cùng file `data/basket-state.sqlite3` qua mỗi lần chạy. State gắn với
  hash login/server và hash cấu hình, không lưu mật khẩu/login dạng rõ.
- Bot chặn mọi lệnh nếu thấy vị thế ngoài magic/symbol hoặc bất kỳ pending
  order nào trong tài khoản. Vị thế cùng magic nhưng không có trong journal
  cũng bị chặn; không tự nhận quản lý rổ không rõ nguồn gốc.
- Có khóa OS theo login (trong thư mục tạm của Windows user), cộng khóa
  theo journal, để các bản sao chạy trên cùng user/VPS không gửi đồng thời.
  Cơ chế này không điều phối nhiều VPS; chỉ dùng một VPS điều khiển tài khoản.
- `EXECUTION_UNCERTAIN` hoặc `PENDING_EXECUTION_REVIEW`: dừng worker, kiểm tra
  Positions/History và Journal trong MT5, so khớp với intent trong SQLite.
  Lỗi gửi, timeout, partial fill, thiếu deal history hoặc crash sau send đều
  khóa các lần gửi tiếp theo. Không có lệnh tự retry hay tự xóa pending.
- Khi cần hỗ trợ đối soát, dùng bản sao journal cục bộ và thông tin giao dịch
  đã che dữ liệu cá nhân. Chưa có công cụ tự sửa pending; phải xác minh và
  sửa trạng thái có kiểm soát trước khi khởi động lại. Đừng xóa journal để
  lách khóa hay tạo journal mới khi vẫn có vị thế.
- Thay tài khoản/cấu hình phải dừng worker, xử lý xong vị thế và pending,
  sao lưu journal, rồi bắt đầu phiên được chủ động đánh giá lại. Đổi state
  làm mất mốc lỗ cũ; không dùng việc này để vượt giới hạn ngày/tuần.
- Nạp/rút/credit hoặc các deal điều chỉnh số dư sau khi khởi tạo được chặn
  với `CASHFLOW_REVIEW`; mốc equity cần được đối soát thủ công.
- Nếu chỉ đóng được lệnh thắng khi Trim, kết quả là `TRIM_WINNER_ONLY`.
  Bot không xem phần lời đó là ngân sách dùng lại vô hạn cho các lần tỉa.

## Phạm vi kiểm chứng

Có kiểm thử planner, gateway qua terminal giả, payload, restart, khóa đồng
thời, chuyển tài khoản, lỗi dữ liệu và chuỗi nhiều tầng. Có regression test
cho PnL thay đổi giữa các lần đọc, spread giãn ngay trước send, giá hết hạn,
ngân sách ngày co lại và thứ tự đóng Hedge làm thay đổi margin.

**Chưa chạy với Windows VPS/terminal LiteFinance thật trong phiên phát triển
này.** CI trên Linux/Windows với terminal giả không xác nhận điều kiện broker, tốc độ khớp, lợi nhuận hay
khả năng chịu gap. SL/risk là ước tính trước gửi; gap, slippage, phí/swap
có thể khiến tổn thất thực tế vượt ước tính. Tính năng không thay thế pipeline
backtest/tick replay hoặc mô hình AI huấn luyện.

Tài liệu MT5 chính thức dùng khi triển khai:
- https://www.mql5.com/en/docs/constants/environment_state/accountinformation
- https://www.mql5.com/en/docs/python_metatrader5/mt5ordercalcmargin_py
- https://www.mql5.com/en/docs/python_metatrader5/mt5ordercheck_py
- https://www.mql5.com/en/docs/python_metatrader5/mt5ordersend_py
- https://www.mql5.com/en/docs/python_metatrader5/mt5historydealsget_py
