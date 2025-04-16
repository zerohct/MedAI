| Trường                      | Kiểu dữ liệu | Mô tả                                                               |
| --------------------------- | ------------ | ------------------------------------------------------------------- |
| disease_name                | string       | Tên của bệnh/chứng mắc được từ Mayo Clinic                          |
| url                         | string       | URL nguồn của trang bệnh từ Mayo Clinic                             |
| source                      | string       | Nguồn dữ liệu (ví dụ: "mayoclinic")                                 |
| description                 | string       | Mô tả chung, tổng quan về bệnh                                      |
| symptoms                    | array/string | Danh sách triệu chứng của bệnh                                      |
| causes                      | array/string | Danh sách nguyên nhân gây ra bệnh                                   |
| risk_factors                | array/string | Các yếu tố nguy cơ liên quan đến bệnh                               |
| complications               | array/string | Danh sách các biến chứng có thể xảy ra của bệnh                     |
| prevention                  | array/string | Các biện pháp phòng ngừa bệnh                                       |
| diagnosis                   | array/string | Phương pháp, xét nghiệm chẩn đoán bệnh                              |
| treatment                   | array/string | Phương pháp điều trị, can thiệp y khoa cho bệnh                     |
| preparing_for_appointment   | array/string | Những lưu ý, hướng dẫn chuẩn bị khi đi khám                         |
| lifestyle_and_home_remedies | array/string | Hướng dẫn về lối sống và biện pháp tự chăm sóc, hỗ trợ tại nhà      |
| alternative_medicine        | array/string | Các phương pháp y học thay thế (nếu có)                             |
| coping_and_support          | array/string | Hỗ trợ tâm lý, thông tin về các nhóm hỗ trợ, cộng đồng đối phó bệnh |
| images                      | array/string | Danh sách URL của hình ảnh liên quan đến bệnh                       |
| scraped_time                | timestamp    | Thời gian thu thập dữ liệu (ví dụ: định dạng ISO 8601)              |
