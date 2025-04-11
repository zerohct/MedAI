import json
import os

class SaveItemPipeline:
    def __init__(self):
        self.counters = {}

    def open_spider(self, spider):
        self.counters[spider.name] = 0
        # Tạo thư mục "data" nếu chưa tồn tại
        self.data_dir = os.path.join(os.getcwd(), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        spider.logger.info(f"Pipeline: Mở kết nối lưu dữ liệu cho {spider.name}")

    def close_spider(self, spider):
        spider.logger.info(f"Pipeline: {spider.name} đã lưu tổng số {self.counters[spider.name]} mục")

    def process_item(self, item, spider):
        self.counters[spider.name] += 1
        # Nếu cần, thực hiện chuẩn hóa triệu chứng
        if 'symptoms' in item:
            # Ví dụ: sử dụng hàm normalize_symptoms nếu đã định nghĩa (xem code trước đó)
            item['symptoms_normalized'] = normalize_symptoms(item['symptoms'])
        
        # Xác định đường dẫn file: lưu trong thư mục "data"
        file_path = os.path.join(self.data_dir, f"data_{spider.name}.jsonl")
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
        spider.logger.info(f"Pipeline: {spider.name} đã lưu {self.counters[spider.name]} mục")
        return item

# Hàm chuẩn hóa các triệu chứng, ví dụ:
SYMPTOM_MAP = {
    'sốt cao': 'sốt',
    'sốt nhẹ': 'sốt',
    'sốt 40 độ': 'sốt',
    'sốt 39 độ': 'sốt',
    'high fever': 'sốt',
    'elevated temperature': 'sốt'
}

def normalize_symptoms(symptom_list):
    normalized = []
    for symptom in symptom_list:
        symptom_lower = symptom.lower().strip()
        found = False
        for key in SYMPTOM_MAP:
            if key in symptom_lower:
                normalized.append(SYMPTOM_MAP[key])
                found = True
                break
        if not found:
            normalized.append(symptom_lower)
    return list(set(normalized))
