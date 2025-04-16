| Trường       | Kiểu dữ liệu  | Mô tả                                  |
| ------------ | ------------- | -------------------------------------- |
| id           | string (UUID) | ID định danh duy nhất của bài viết     |
| name         | string        | Tên của bệnh/chứng mắc được từ Vinmec  |
| url          | string        | URL nguồn của trang bệnh từ Vinmec     |
| source       | string        | Nguồn dữ liệu (mặc định: "vinmec")     |
| description  | array/string  | Mô tả chung, tổng quan về bệnh         |
| symptoms     | array/string  | Danh sách triệu chứng của bệnh         |
| causes       | array/string  | Danh sách nguyên nhân gây ra bệnh      |
| risk_factors | array/string  | Các yếu tố nguy cơ liên quan đến bệnh  |
| diagnosis    | array/string  | Phương pháp, xét nghiệm chẩn đoán bệnh |
| treatment    | array/string  | Phương pháp điều trị bệnh              |
| prevention   | array/string  | Các biện pháp phòng ngừa bệnh          |
| images       | array/string  | Danh sách URL của hình ảnh liên quan   |
| videos       | array/string  | Danh sách URL của video liên quan      |
| extracted_at | timestamp     | Thời gian thu thập dữ liệu             |
| metadata     | object        | Thông tin metadata bổ sung (nếu có)    |
