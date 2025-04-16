### Ngày 3

# 1. Cải tiến việc cào dữ liệu pubmed, vinmec, mayo

### Tiến độ hiện tại

- Đã nâng cấp thuật toán cào dữ liệu, cải thiện độ chính xác lên 20% so với phiên bản trước
- Đã xử lý các trường hợp lỗi phổ biến khi trích xuất dữ liệu từ cấu trúc HTML phức tạp

### Vấn đề tồn đọng

- Một số trường hợp đặc biệt vẫn chưa được xử lý đúng cách
- Cần cải thiện khả năng xử lý dữ liệu động được tải bằng JavaScript

### Kế hoạch tiếp theo

- Nghiên cứu phương pháp cào dữ liệu thay thế sử dụng API nếu có
- Tích hợp cơ chế bộ nhớ đệm để giảm số lượng yêu cầu đến máy chủ
- Xây dựng hệ thống quản lý lỗi và tự động thử lại cho các mục không thành công

# 2. Chuẩn hóa dữ liệu ban đầu

### Tiến độ hiện tại

- Đã xây dựng quy trình mã hóa cơ bản cho dữ liệu thu thập
- Bắt đầu áp dụng tiêu chuẩn hóa định dạng văn bản và metadata
- Xây dựng cấu trúc dữ liệu thống nhất giữa các nguồn khác nhau

### Vấn đề tồn đọng

- Còn xuất hiện một số lỗi không nhất quán giữa các nguồn dữ liệu
- Cần cải thiện quy trình chuẩn hóa từ vựng y khoa
  Quá trình loại bỏ thông tin trùng lặp chưa hoàn chỉnh

### Kế hoạch tiếp theo

- Hoàn thiện các công cụ xử lý và chuẩn hóa dữ liệu
- Triển khai kiểm tra chất lượng tự động cho dữ liệu sau khi chuẩn hóa
- Xây dựng cơ sở dữ liệu tạm thời để lưu trữ dữ liệu đã chuẩn hóa
