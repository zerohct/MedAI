from sentence_transformers import SentenceTransformer

# Chọn mô hình embedding phù hợp (ví dụ: all-MiniLM-L6-v2)
model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_text(text):
    """Nhận vào một chuỗi văn bản và trả về embedding vector dưới dạng list."""
    return model.encode(text).tolist()

def add_embeddings(item, fields_to_embed=None):
    """
    Thêm trường embedding cho các trường văn bản cần chuyển đổi.
    fields_to_embed là danh sách các key của item mà bạn muốn tạo embedding.
    Ví dụ: ['description', 'abstract']
    """
    if fields_to_embed is None:
        fields_to_embed = ['description', 'abstract']
    
    for field in fields_to_embed:
        if field in item and item[field]:
            item[f"{field}_embedding"] = embed_text(item[field])
    return item
