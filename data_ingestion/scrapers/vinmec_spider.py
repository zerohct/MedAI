import scrapy
import logging
import re
import json
from urllib.parse import urljoin

class VinmecSpider(scrapy.Spider):
    name = 'vinmec'
    allowed_domains = ['vinmec.com']
    # Thay đổi URL bắt đầu - sử dụng sitemap hoặc danh mục chữ cái
    start_urls = [
        'https://www.vinmec.com/vie/benh/',  # Trang chính liệt kê bệnh
        'https://www.vinmec.com/sitemap.xml'  # Sitemap để lấy nhiều URL hơn
    ]
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'DOWNLOAD_DELAY': 1,  # Giảm delay xuống để tăng tốc độ cào
        'ROBOTSTXT_OBEY': False,
        'LOG_LEVEL': 'INFO',
        'COOKIES_ENABLED': True,
        'DOWNLOAD_TIMEOUT': 60,
        'RETRY_TIMES': 3,
        'CONCURRENT_REQUESTS': 4,  # Tăng số lượng request đồng thời
    }
    
    def __init__(self, *args, **kwargs):
        super(VinmecSpider, self).__init__(*args, **kwargs)
        self.parsed_urls = set()  # Tập hợp các URL đã xử lý để tránh trùng lặp
        self.disease_count = 0  # Đếm số lượng bệnh đã cào
    
    def start_requests(self):
        """Xử lý các request ban đầu với headers thích hợp"""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.vinmec.com/',
        }
        
        for url in self.start_urls:
            self.logger.info(f"VinmecSpider: Bắt đầu thu thập dữ liệu từ: {url}")
            if 'sitemap.xml' in url:
                yield scrapy.Request(url, callback=self.parse_sitemap, headers=headers)
            else:
                yield scrapy.Request(url, callback=self.parse_list_page, headers=headers)
    
    def parse_sitemap(self, response):
        """Phân tích sitemap để tìm tất cả các URL bệnh"""
        self.logger.info(f"VinmecSpider: Đang phân tích sitemap: {response.url}")
        
        # Tìm tất cả các URL trong sitemap
        urls = re.findall(r'<loc>(.*?)</loc>', response.text)
        
        # Lọc URL liên quan đến bệnh
        disease_urls = [url for url in urls if '/benh/' in url]
        self.logger.info(f"VinmecSpider: Tìm thấy {len(disease_urls)} liên kết bệnh từ sitemap")
        
        # Theo dõi mỗi URL bệnh
        for url in disease_urls:
            if url not in self.parsed_urls:
                self.parsed_urls.add(url)
                yield scrapy.Request(
                    url, 
                    callback=self.parse_disease_page,
                    headers={'Referer': response.url}
                )
        
        # Tìm và theo dõi các sitemap con
        sub_sitemaps = re.findall(r'<sitemap>\s*<loc>(.*?)</loc>', response.text)
        for sitemap in sub_sitemaps:
            yield scrapy.Request(
                sitemap,
                callback=self.parse_sitemap,
                headers={'Referer': response.url}
            )
    
    def parse_list_page(self, response):
        """Phân tích trang danh sách bệnh và thu thập các liên kết"""
        self.logger.info(f"VinmecSpider: Đang phân tích trang danh sách tại: {response.url}")
        
        # PHƯƠNG PHÁP 1: Tìm các liên kết bệnh trên trang hiện tại
        all_links = response.css('a::attr(href)').getall()
        disease_links = [link for link in all_links if '/benh/' in link and link != '/vie/benh/' and link != '/vi/benh/']
        disease_links = list(set(disease_links))  # Loại bỏ trùng lặp
        
        self.logger.info(f"VinmecSpider: Tìm thấy {len(disease_links)} liên kết bệnh độc nhất trên trang này")
        
        # Xử lý mỗi liên kết bệnh
        for link in disease_links:
            absolute_url = response.urljoin(link)
            if absolute_url not in self.parsed_urls:
                self.parsed_urls.add(absolute_url)
                self.logger.info(f"VinmecSpider: Theo dõi liên kết bệnh: {absolute_url}")
                yield scrapy.Request(
                    absolute_url, 
                    callback=self.parse_disease_page,
                    headers={'Referer': response.url}
                )
        
        # PHƯƠNG PHÁP 2: Tìm liên kết đến các trang danh sách khác
        # Kiểm tra các liên kết phân trang
        next_page_selectors = [
            'a.next::attr(href)',
            'a.pagination-next::attr(href)',
            'li.next a::attr(href)',
            'a:contains("Tiếp")::attr(href)',
            '.pagination a[rel="next"]::attr(href)',
            '.pager__item--next a::attr(href)'
        ]
        
        next_page = None
        for selector in next_page_selectors:
            next_page = response.css(selector).get()
            if next_page:
                break
        
        if next_page:
            next_url = response.urljoin(next_page)
            if next_url not in self.parsed_urls:
                self.parsed_urls.add(next_url)
                self.logger.info(f"VinmecSpider: Chuyển sang trang tiếp theo: {next_url}")
                yield scrapy.Request(
                    next_url, 
                    callback=self.parse_list_page,
                    headers={'Referer': response.url}
                )
        
        # PHƯƠNG PHÁP 3: Tìm liên kết đến các danh mục bệnh theo chữ cái
        alphabet_selectors = [
            '.vm-az-list a::attr(href)',
            '.block-az-list a::attr(href)',
            '.alphabet-navigation a::attr(href)',
            '.az-index a::attr(href)'
        ]
        
        alphabet_links = []
        for selector in alphabet_selectors:
            links = response.css(selector).getall()
            if links:
                alphabet_links.extend(links)
        
        if alphabet_links:
            self.logger.info(f"VinmecSpider: Tìm thấy {len(alphabet_links)} liên kết bảng chữ cái")
            for link in alphabet_links:
                absolute_url = response.urljoin(link)
                if absolute_url not in self.parsed_urls:
                    self.parsed_urls.add(absolute_url)
                    self.logger.info(f"VinmecSpider: Theo dõi liên kết bảng chữ cái: {absolute_url}")
                    yield scrapy.Request(
                        absolute_url, 
                        callback=self.parse_list_page,
                        headers={'Referer': response.url}
                    )
        
        # PHƯƠNG PHÁP 4: Tìm các danh mục bệnh
        category_selectors = [
            '.category-list a::attr(href)',
            '.vm-category a::attr(href)',
            '.menu-item a[href*="/benh/"]::attr(href)',
            '.navigation a[href*="/benh/"]::attr(href)'
        ]
        
        category_links = []
        for selector in category_selectors:
            links = response.css(selector).getall()
            if links:
                category_links.extend(links)
        
        if category_links:
            self.logger.info(f"VinmecSpider: Tìm thấy {len(category_links)} liên kết danh mục")
            for link in category_links:
                absolute_url = response.urljoin(link)
                if absolute_url not in self.parsed_urls and '/benh/' in absolute_url:
                    self.parsed_urls.add(absolute_url)
                    self.logger.info(f"VinmecSpider: Theo dõi liên kết danh mục: {absolute_url}")
                    yield scrapy.Request(
                        absolute_url, 
                        callback=self.parse_list_page,
                        headers={'Referer': response.url}
                    )
    
    def parse_disease_page(self, response):
        """Phân tích trang bệnh cụ thể với khả năng trích xuất nội dung tốt hơn"""
        self.disease_count += 1
        self.logger.info(f"VinmecSpider: Đang phân tích trang bệnh [{self.disease_count}]: {response.url}")
        
        # Thử các phương pháp khác nhau để trích xuất tên bệnh
        disease_name = None
        
        # Phương pháp 1: Tìm thẻ <h1>
        h1_text = response.css('h1::text').get()
        if h1_text and h1_text.strip():
            disease_name = h1_text.strip()
        
        if not disease_name:
            # Phương pháp 2: Tìm các lớp tiêu đề phổ biến
            title_text = response.css('.article-title::text, .page-title::text, .section-heading::text, .title::text').get()
            if title_text and title_text.strip():
                disease_name = title_text.strip()
        
        if not disease_name:
            # Phương pháp 3: Tìm trong meta title
            meta_title = response.css('meta[property="og:title"]::attr(content), title::text').get()
            if meta_title and meta_title.strip():
                disease_name = meta_title.strip()
                # Loại bỏ phần "| Vinmec" nếu có
                disease_name = re.sub(r'\s*\|\s*Vinmec.*$', '', disease_name)
        
        if not disease_name:
            # Phương pháp dự phòng: Trích xuất từ URL
            disease_slug = response.url.split('/')[-1]
            parts = re.sub(r'-\d+$', '', disease_slug).split('-')  # Loại bỏ số ID ở cuối
            disease_name = ' '.join(parts).title()
        
        disease_name = disease_name.strip() if disease_name else "Unknown Disease"
        
        # Trích xuất HTML nội dung
        content_html = ''
        
        # Phương pháp 1: Tìm khu vực nội dung chính
        content_selectors = [
            '.article-content', '.content-detail', '.vm-article-content', 
            '.vm-content', '#mainContent', 'main', '.node__content',
            '.field--name-body', '.content', 'article'
        ]
        
        for selector in content_selectors:
            content = response.css(selector)
            if content:
                content_html = content.get() or ''
                if content_html:
                    break
        
        # Phương pháp 2: Nếu không tìm thấy khu vực nội dung cụ thể, sử dụng toàn bộ body
        if not content_html:
            content_html = response.css('body').get() or ''
        
        # Tạo các mẫu regex để tìm các phần trong HTML
        section_patterns = {
            'description': r'(?:<h2[^>]*>|<h3[^>]*>|<strong[^>]*>)([^<]*?(?:giới thiệu|tổng quan|mô tả|khái quát)[^<]*?)(?:</h2>|</h3>|</strong>)(.*?)(?:<h2|<h3|<strong)',
            'symptoms': r'(?:<h2[^>]*>|<h3[^>]*>|<strong[^>]*>)([^<]*?(?:triệu chứng|biểu hiện|dấu hiệu)[^<]*?)(?:</h2>|</h3>|</strong>)(.*?)(?:<h2|<h3|<strong)',
            'causes': r'(?:<h2[^>]*>|<h3[^>]*>|<strong[^>]*>)([^<]*?(?:nguyên nhân)[^<]*?)(?:</h2>|</h3>|</strong>)(.*?)(?:<h2|<h3|<strong)',
            'risk_factors': r'(?:<h2[^>]*>|<h3[^>]*>|<strong[^>]*>)([^<]*?(?:yếu tố nguy cơ|nguy cơ)[^<]*?)(?:</h2>|</h3>|</strong>)(.*?)(?:<h2|<h3|<strong)',
            'diagnosis': r'(?:<h2[^>]*>|<h3[^>]*>|<strong[^>]*>)([^<]*?(?:chẩn đoán)[^<]*?)(?:</h2>|</h3>|</strong>)(.*?)(?:<h2|<h3|<strong)',
            'treatment': r'(?:<h2[^>]*>|<h3[^>]*>|<strong[^>]*>)([^<]*?(?:điều trị|phương pháp điều trị|cách điều trị)[^<]*?)(?:</h2>|</h3>|</strong>)(.*?)(?:<h2|<h3|<strong)',
            'prevention': r'(?:<h2[^>]*>|<h3[^>]*>|<strong[^>]*>)([^<]*?(?:phòng ngừa|cách phòng)[^<]*?)(?:</h2>|</h3>|</strong>)(.*?)(?:<h2|<h3|<strong)',
        }
        
        # Phương pháp trích xuất dự phòng nếu các mẫu regex không hoạt động
        fallback_section_selectors = {
            'description': ['p:first-of-type', '.introduction', '.summary'],
            'symptoms': ['h2:contains("Triệu chứng") + *', 'h3:contains("Triệu chứng") + *'],
            'causes': ['h2:contains("Nguyên nhân") + *', 'h3:contains("Nguyên nhân") + *'],
            'risk_factors': ['h2:contains("Yếu tố nguy cơ") + *', 'h3:contains("Yếu tố nguy cơ") + *'],
            'diagnosis': ['h2:contains("Chẩn đoán") + *', 'h3:contains("Chẩn đoán") + *'],
            'treatment': ['h2:contains("Điều trị") + *', 'h3:contains("Điều trị") + *'],
            'prevention': ['h2:contains("Phòng ngừa") + *', 'h3:contains("Phòng ngừa") + *'],
        }
        
        # Trích xuất các phần bằng mẫu regex
        sections = {}
        for section_name, pattern in section_patterns.items():
            matches = re.search(pattern, content_html, re.DOTALL | re.IGNORECASE)
            if matches:
                # Làm sạch HTML đã trích xuất
                section_html = matches.group(2)
                # Trích xuất văn bản từ các mục danh sách nếu có
                list_items = re.findall(r'<li[^>]*>(.*?)</li>', section_html, re.DOTALL)
                if list_items:
                    # Nếu tìm thấy các mục danh sách, sử dụng chúng
                    clean_items = []
                    for item in list_items:
                        # Loại bỏ thẻ HTML
                        clean_item = re.sub(r'<[^>]+>', ' ', item)
                        # Làm sạch khoảng trắng
                        clean_item = re.sub(r'\s+', ' ', clean_item).strip()
                        if clean_item:
                            clean_items.append(clean_item)
                    sections[section_name] = clean_items
                else:
                    # Nếu không có mục danh sách, trích xuất văn bản từ đoạn văn
                    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', section_html, re.DOTALL)
                    if paragraphs:
                        # Làm sạch thẻ HTML từ đoạn văn
                        clean_paras = []
                        for para in paragraphs:
                            # Loại bỏ thẻ HTML
                            clean_para = re.sub(r'<[^>]+>', ' ', para)
                            # Làm sạch khoảng trắng
                            clean_para = re.sub(r'\s+', ' ', clean_para).strip()
                            if clean_para:
                                clean_paras.append(clean_para)
                        sections[section_name] = clean_paras
                    else:
                        # Phương án cuối cùng: chỉ cần làm sạch tất cả các thẻ HTML từ phần
                        clean_text = re.sub(r'<[^>]+>', ' ', section_html)
                        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                        if clean_text:
                            sections[section_name] = [clean_text]
        
        # Thử phương pháp dự phòng nếu không tìm thấy các phần bằng regex
        for section_name, selectors in fallback_section_selectors.items():
            if section_name not in sections:
                for selector in selectors:
                    selected_content = response.css(selector)
                    if selected_content:
                        text_content = selected_content.css('::text').getall()
                        if text_content:
                            clean_text = ' '.join([t.strip() for t in text_content if t.strip()])
                            if clean_text:
                                sections[section_name] = [clean_text]
                                break
        
        # Nếu không tìm thấy mô tả bằng regex, cố gắng trích xuất vài đoạn văn đầu tiên
        if 'description' not in sections:
            first_paragraphs = response.css('p::text').getall()[:3]
            if first_paragraphs:
                clean_text = " ".join([p.strip() for p in first_paragraphs if p.strip()])
                if clean_text:
                    sections['description'] = [clean_text]
        
        # # Trích xuất hình ảnh
        # images = response.css('img::attr(src)').getall()
        # # Làm cho URL hình ảnh tuyệt đối
        # images = [response.urljoin(img) for img in images if img and not img.startswith('data:')]
        
        # Trích xuất video
        videos = response.css('iframe::attr(src)').getall()
        
        # Xây dựng mục cuối cùng
        item = {
            'source': 'vinmec',
            'url': response.url,
            'disease_name': disease_name,

            'videos': videos,
        }
        
        # Thêm các phần đã trích xuất vào mục
        for section_name, content in sections.items():
            item[section_name] = content
        
        # Nếu vẫn không có mô tả, thêm một placeholder
        if 'description' not in item:
            item['description'] = ["Thông tin bệnh " + disease_name]
        
        self.logger.info(f"VinmecSpider: Đã thu thập dữ liệu cho bệnh: {item['disease_name']}")
        yield item

    def closed(self, reason):
        """Được gọi khi spider đóng, báo cáo tổng số lượng bệnh đã cào"""
        self.logger.info(f"VinmecSpider: Đã cào tổng cộng {self.disease_count} bệnh")
        self.logger.info(f"VinmecSpider: Đã duyệt tổng cộng {len(self.parsed_urls)} URL")