# Quản lý rổ lệnh XAUUSD theo danh sách người dùng

## Mục tiêu và phạm vi
Bổ sung cả năm nhóm tính năng trong ảnh người dùng ngày 20/10/2026 vào
PR #28: Hedge nhiều tầng, DCA trước/sau Hedge, Pyramiding, Trim và giới hạn
lot/ký quỹ. Đây là thuật toán độc lập theo mô tả tính năng, không xác nhận
hành vi hay hiệu quả của sản phẩm VTrade. Tiếp tục dùng Python trên Windows
VPS, USD và đòn bẩy 1:50. Không chạy giao dịch từ môi trường phát triển này.

## Thiết kế
- Giữ nguyên worker giám sát và TradingPolicy hiện có. Thêm `app.basket`
  với chế độ mặc định preview; `--execute-demo` mới cho phép gửi lệnh Demo.
  Không có chế độ Live. Yêu cầu Demo + hedging + hedge_allowed + không FIFO.
- Chỉ quản lý vị thế XAUUSD có magic riêng; nếu tài khoản có vị thế hoặc
  pending order ngoài phạm vi bot, dừng mở/đóng tự động để không ảnh hưởng
  lệnh của người dùng. State khóa theo hash tài khoản + cấu hình.
- Một chu kỳ chỉ làm một quyết định: thoát rổ khi vượt ngân sách/lãi mục
  tiêu, Trim, Hedge, DCA, Pyramiding hoặc vào lệnh theo EMA đa khung.
- DCA và Hedge theo khoảng cách adverse tính từ giá seed; cấu hình khoảng
  cách DCA trước/sau Hedge độc lập. Hedge được chốt trạng thái đến khi rổ
  rỗng. Các bộ đếm chỉ tăng sau khi lệnh xác nhận khớp đầy đủ và không giảm
  khi tỉa hoặc chạm SL; không tăng lot theo cấp số nhân.
- Pyramiding chỉ khi tất cả lệnh hướng chính có lãi sau dự trù chi phí,
  tín hiệu vẫn cùng hướng và chưa từng Hedge trong rổ hiện tại.
- Trim đóng nguyên ticket thắng trước, xác minh lợi nhuận đã thực hiện từ
  deal history, rồi mới đóng ticket lỗ nếu đủ bù lỗ và buffer. Không giả
  định hai lệnh đóng là nguyên tử; không dùng lợi nhuận nổi làm tiền đã thu.
- Mỗi lệnh mới có SL, đúng lot/tick grid. Ngân sách lệnh tối đa 0,5% equity,
  tổng phần lỗ còn lại tới SL tối đa 1%; giới hạn ngày/tuần 2%/5%, giữ ít
  nhất 30% equity dưới dạng free margin. Không tính giảm risk vì có hedge.
  Kiểm tra cả order_calc_margin và order_check ngay trước order_send.
- Giá trị mặc định minh họa: 0,01 lot/lệnh, 6 vị thế, tổng 0,06 lot,
  DCA trước Hedge 300 points, sau Hedge 900/1500 points; Hedge 600/1200
  points với tỷ lệ 50%/100% khối lượng hướng chính; pyramid mỗi 300 points,
  tối đa 2 tầng; SL 2000 points. Đây không phải khuyến nghị giao dịch.
- Journal SQLite ghi intent trước khi gửi lệnh, có khóa một tiến trình,
  commit state sau khi xác minh khớp. Lệnh lỗi/timeout/khớp một phần hoặc
  trạng thái không rõ làm khóa execution, không retry tự động. SL vẫn nằm
  tại broker. Không tự phục hồi state hỏng hoặc xóa lịch sử khi restart.
- Stop loss/trim/thoát rổ được xem xét trước bộ lọc mở lệnh (spread, giờ,
  mục tiêu ngày). Chỉ dữ liệu hợp lệ và tài khoản đã xác minh mới được dùng.
- Trình điều khiển xuất JSON tương thích dashboard, gồm phase/counters,
  tổng lot, PnL rổ, quyết định và lý do chặn. Không lưu mật khẩu/account ID.

## Tiêu chí kiểm thử
Kiểm thử planner bằng dữ liệu xác định cho BUY/SELL, tất cả cơ chế và
ưu tiên; xác nhận giới hạn lot/risk/margin và dữ liệu NaN/mất dữ liệu bị
chặn; dùng terminal giả ở ranh giới MT5 để kiểm tra Demo, hedging,
order_check, payload close có position ticket, không đóng nhầm vị thế,
không retry sau timeout/partial fill và không tỉa lệnh lỗ trước khi xác
nhận lời. Kiểm thử restart, thay tài khoản/config và khóa đồng thời.
Chạy pytest, ruff, bandit, GitHub CI. Kiểm thử Windows/MT5 thực tế còn phải
thực hiện tại VPS; CI Linux/Windows giả lập không chứng nhận chiến lược hay broker.
