### Ngày 2:

# 0. Phân tích

- Xác định WHO API không còn ổn định → loại bỏ
- Thay thế bằng PubMed, Mayo Clinic, vinmec
- Tạo lại module crawler vinmec + Mayo + PubMed

# 1. PubMed

- Tạo PubMed spider để thu thập dữ liệu từ pubmed.gov
- Triển khai trong `pubmed_spider.py`
- Thu thập thông tin bệnh, bao gồm các nghiên cứu và bài báo khoa học

# 2. Mayo Clinic

- Triển khai spider trong `mayoclinic_spider.py`
- Cấu trúc thu thập:
  - Bắt đầu từ danh sách bệnh theo chữ cái (A-Z)
  - Thu thập thông tin chi tiết bao gồm:
    - Tên bệnh
    - Mô tả
    - Triệu chứng
    - Nguyên nhân
    - Cách điều trị
    - Hình ảnh liên quan
- Xử lý phân trang và điều hướng thông minh

# 3. Vinmec

- Triển khai spider trong `vinmec_spider.py`
- Tính năng chính:
  - Crawler thông minh với nhiều phương pháp thu thập:
    - Thu thập từ sitemap
    - Thu thập theo danh mục bệnh
    - Thu thập theo bảng chữ cái
    - Xử lý phân trang
  - Thu thập thông tin chi tiết:
    - Tên bệnh
    - Mô tả
    - Triệu chứng
    - Nguyên nhân
    - Yếu tố nguy cơ
    - Chẩn đoán
    - Phương pháp điều trị
    - Phòng ngừa
  - Tính năng nâng cao:
    - Tránh trùng lặp URL
    - Theo dõi số lượng bệnh đã cào
    - Xử lý lỗi và retry
    - Custom user agent và delay
    - Logging chi tiết

# 4. Kết quả

- Đã triển khai thành công 3 spider chính
- Thu thập được dữ liệu đa dạng từ nhiều nguồn
- Chuẩn bị cho bước tiếp theo: chuẩn hóa và tích hợp dữ liệu
