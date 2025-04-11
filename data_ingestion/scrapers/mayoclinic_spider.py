import scrapy
import string

class MayoClinicSpider(scrapy.Spider):
    name = "mayoclinic"
    allowed_domains = ["mayoclinic.org"]
    
    def start_requests(self):
        """Tạo các requests ban đầu cho từng chữ cái (A-Z)"""
        self.logger.info("MayoClinicSpider: Đang cào danh sách bệnh từ Mayo Clinic")
        
        # Tạo URLs cho các trang danh sách bệnh theo chữ cái
        for letter in ["A"]:
            url = f"https://www.mayoclinic.org/diseases-conditions/index?letter={letter}"
            self.logger.info(f"Bắt đầu cào danh sách bệnh bắt đầu bằng chữ: {letter}")
            yield scrapy.Request(url, callback=self.parse_disease_list)
    
    def parse_disease_list(self, response):
        """Xử lý trang danh sách bệnh theo chữ cái"""
        letter = response.url.split("letter=")[1] if "letter=" in response.url else "Unknown"
        self.logger.info(f"Đang xử lý danh sách bệnh bắt đầu bằng chữ {letter}: {response.url}")
        
        # Lấy danh sách liên kết đến từng bệnh cụ thể
        disease_links = response.css('.cmp-list--alphabetical li a::attr(href)').getall()
        
        # Fallback nếu không tìm thấy liên kết với selector ở trên
        if not disease_links:
            self.logger.info(f"Không tìm thấy liên kết bệnh với selector chính. Đang thử selector thay thế.")
            
            # Thử nhiều selector thay thế
            alternative_selectors = [
                'ul.alphabetical-index li a::attr(href)',
                'div.index li a::attr(href)',
                'ul li a::attr(href)'
            ]
            
            for selector in alternative_selectors:
                disease_links = response.css(selector).getall()
                if disease_links:
                    self.logger.info(f"Tìm thấy liên kết với selector thay thế: {selector}")
                    # Lọc để chỉ lấy các liên kết liên quan đến bệnh
                    disease_links = [link for link in disease_links if '/diseases-conditions/' in link and not '/index' in link]
                    if disease_links:
                        break
        
        self.logger.info(f"Tìm thấy {len(disease_links)} bệnh bắt đầu bằng chữ {letter}")
        
        # Giới hạn số lượng bệnh để test
        # disease_links = disease_links[:3]  # Chỉ lấy 3 bệnh đầu tiên để test
        
        for link in disease_links:
            full_url = response.urljoin(link)
            self.logger.info(f"Theo dõi liên kết bệnh: {full_url}")
            yield scrapy.Request(full_url, callback=self.parse_disease)
    
    def parse_disease(self, response):
        """Phân tích trang chi tiết về bệnh"""
        self.logger.info(f"Đang cào thông tin bệnh từ: {response.url}")
        
        # Trích xuất tên bệnh
        disease_name = response.css('h1::text').get()
        if not disease_name:
            disease_name = response.xpath('//h1//text()').get()
        
        # Trích xuất các đoạn văn mô tả
        description_paragraphs = response.css('#main article p::text, #main article p *::text').getall()
        if not description_paragraphs:
            description_paragraphs = response.css('div[id="main"] p::text, div[id="main"] p *::text').getall()
        
        description = " ".join([p.strip() for p in description_paragraphs if p.strip()])
        
        # Hàm helper để trích xuất nội dung từ một phần cụ thể
        def extract_section(heading_text):
            # Tìm h2 hoặc h3 có chứa text
            heading = response.xpath(f'//h2[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{heading_text.lower()}")]/parent::*')
            if not heading:
                heading = response.xpath(f'//h3[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{heading_text.lower()}")]/parent::*')
            
            if not heading:
                return []
                
            # Lấy nội dung từ các phần tử list item sau heading
            content = []
            content = heading.css('ul li::text, ul li *::text').getall()
            
            # Nếu không có list, thử lấy nội dung từ đoạn văn
            if not content:
                content = heading.css('p::text, p *::text').getall()
                
            return [item.strip() for item in content if item.strip()]
        
        # Trích xuất triệu chứng, nguyên nhân và điều trị
        symptoms = extract_section("symptom")
        causes = extract_section("cause")
        treatment = extract_section("treatment")
        
        # Trích xuất hình ảnh
        images = response.css('#main article img::attr(src)').getall()
        if not images:
            images = response.css('div[id="main"] img::attr(src)').getall()
        
        # Tạo item để trả về
        item = {
            'source': 'mayoclinic',
            'url': response.url,
            'disease_name': disease_name.strip() if disease_name else '',
            'description': description,
            'symptoms': symptoms,
            'causes': causes,
            'treatment': treatment,
            'images': images
        }
        
        self.logger.info(f"Đã cào bệnh: {item['disease_name'] or 'Không xác định'}")
        
        # Debug thông tin trích xuất
        for key, value in item.items():
            if key != 'url' and key != 'source':
                if isinstance(value, list):
                    self.logger.info(f"  {key}: {len(value)} mục")
                else:
                    preview = value[:50] + "..." if value and len(value) > 50 else value
                    self.logger.info(f"  {key}: {preview}")
        
        yield item