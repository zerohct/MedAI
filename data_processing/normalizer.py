import re

# Định nghĩa từ điển chuyển đổi thuật ngữ
SYMPTOM_MAP = {
    'sốt cao': 'sốt',
    'sốt nhẹ': 'sốt',
    'sốt 40 độ': 'sốt',
    'sốt 39 độ': 'sốt',
    'high fever': 'sốt',
    'elevated temperature': 'sốt'
}

def normalize_symptoms(symptom_list):
    """Chuẩn hóa danh sách triệu chứng thành dạng chuẩn (ví dụ: chuyển 'sốt cao' thành 'sốt')."""
    normalized = []
    for symptom in symptom_list:
        symptom_lower = symptom.lower().strip()
        found = False
        for key, value in SYMPTOM_MAP.items():
            if key in symptom_lower:
                normalized.append(value)
                found = True
                break
        if not found:
            normalized.append(symptom_lower)
    # Loại bỏ trùng lặp nếu có
    return list(set(normalized))

# def normalize_symptoms(symptom_list):
#     normalized = []
#     # Danh sách từ khóa để xác định triệu chứng đơn giản
#     symptom_keywords = ["sốt", "đau", "khó thở", "mệt mỏi", "sưng", "đỏ"]
#     for symptom in symptom_list:
#         symptom = symptom.lower().strip()
#         # Nếu chuỗi quá dài thì có thể không phải triệu chứng đơn giản
#         if len(symptom) > 100:
#             continue
#         found = False
#         for key in symptom_keywords:
#             if key in symptom:
#                 normalized.append(key)
#                 found = True
#                 break
#         if not found:
#             normalized.append(symptom)
#     return list(set(normalized))

def clean_text(text):
    """Loại bỏ các ký tự không cần thiết và chuẩn hóa khoảng trắng cho text."""
    # Loại bỏ HTML tags nếu có
    text = re.sub(r'<.*?>', ' ', text)
    # Thay thế nhiều khoảng trắng thành 1 khoảng trắng
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def normalize_item(item):
    """
    Nhận vào một item (dict) và xử lý các trường văn bản:
      - Chuẩn hóa trường description, abstract.
      - Nếu có trường symptoms, chuẩn hóa theo từ điển.
    """
    if 'description' in item and item['description']:
        item['description'] = clean_text(item['description'])
    if 'abstract' in item and item['abstract']:
        item['abstract'] = clean_text(item['abstract'])
    if 'symptoms' in item:
        item['symptoms_normalized'] = normalize_symptoms(item['symptoms'])
    return item
