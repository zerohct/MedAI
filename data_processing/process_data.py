import os
import json
from normalizer import normalize_item
from embedding_generator import add_embeddings

INPUT_DIR = os.path.join(os.getcwd(), "data")  # Thư mục được tạo bởi giai đoạn 1
OUTPUT_DIR = os.path.join(os.getcwd(), "processed_data")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_file(filename):
    input_path = os.path.join(INPUT_DIR, filename)
    output_path = os.path.join(OUTPUT_DIR, f"processed_{filename}")
    processed_items = []
    
    with open(input_path, "r", encoding="utf-8") as f_in, open(output_path, "w", encoding="utf-8") as f_out:
        for line in f_in:
            try:
                item = json.loads(line)
                # Áp dụng normalize: làm sạch text và chuyển đổi triệu chứng
                item = normalize_item(item)
                # Thêm embedding cho các trường văn bản
                item = add_embeddings(item, fields_to_embed=['description', 'abstract'])
                processed_items.append(item)
                # Ghi ra file JSON dòng
                f_out.write(json.dumps(item, ensure_ascii=False) + "\n")
            except Exception as e:
                print(f"Error processing line: {e}")
    print(f"Xử lý file {filename} thành công, đã lưu tại {output_path}")

def process_all_files():
    # Xét tất cả các file JSONL trong thư mục INPUT_DIR (ví dụ: data_pubmed.jsonl, data_vinmec.jsonl, ...)
    for file in os.listdir(INPUT_DIR):
        if file.endswith(".jsonl"):
            print(f"Đang xử lý {file} ...")
            process_file(file)

if __name__ == '__main__':
    process_all_files()
