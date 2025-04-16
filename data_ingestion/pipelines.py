import json
import os

class SaveRawItemPipeline:
    """
    Pipeline để lưu dữ liệu thô (raw data) vào thư mục data/raw/data_{spider.name}.json
    """
    def __init__(self):
        self.counters = {}

    def open_spider(self, spider):
        self.counters[spider.name] = 0
        # Tạo thư mục data/raw nếu chưa tồn tại
        self.raw_data_dir = os.path.join(os.getcwd(), "data", "raw")
        os.makedirs(self.raw_data_dir, exist_ok=True)
        spider.logger.info(f"Pipeline: Bắt đầu lưu dữ liệu RAW cho spider {spider.name}")

    def close_spider(self, spider):
        spider.logger.info(
            f"Pipeline: {spider.name} đã lưu tổng cộng {self.counters[spider.name]} mục dữ liệu thô (RAW)."
        )

    def process_item(self, item, spider):
        self.counters[spider.name] += 1
        file_path = os.path.join(self.raw_data_dir, f"data_{spider.name}.json")
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(dict(item), ensure_ascii=False) + "\n")
        
        spider.logger.info(
            f"Pipeline: {spider.name} đã lưu {self.counters[spider.name]} mục RAW"
        )
        return item
