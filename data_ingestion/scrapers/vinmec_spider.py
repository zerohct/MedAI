import scrapy
import re
import uuid

class VinmecSpider(scrapy.Spider):
    name = 'vinmec'
    allowed_domains = ['vinmec.com']
    start_urls = [
        'https://www.vinmec.com/vie/benh/',
        'https://www.vinmec.com/sitemap.xml'
    ]
    
    
    def __init__(self, *args, **kwargs):
        super(VinmecSpider, self).__init__(*args, **kwargs)
        self.parsed_urls = set()
        self.disease_count = 0

    def start_requests(self):
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
        self.logger.info(f"VinmecSpider: Phân tích sitemap: {response.url}")
        urls = re.findall(r'<loc>(.*?)</loc>', response.text)
        disease_urls = [url for url in urls if '/benh/' in url]
        self.logger.info(f"VinmecSpider: Tìm thấy {len(disease_urls)} liên kết bệnh từ sitemap")
        for url in disease_urls:
            if url not in self.parsed_urls:
                self.parsed_urls.add(url)
                yield scrapy.Request(url, callback=self.parse_disease_page, headers={'Referer': response.url})
        sub_sitemaps = re.findall(r'<sitemap>\s*<loc>(.*?)</loc>', response.text)
        for sitemap in sub_sitemaps:
            yield scrapy.Request(sitemap, callback=self.parse_sitemap, headers={'Referer': response.url})
    
    def parse_list_page(self, response):
        self.logger.info(f"VinmecSpider: Phân tích trang danh sách tại: {response.url}")
        all_links = response.css('a::attr(href)').getall()
        disease_links = [link for link in all_links if '/benh/' in link and link not in ['/vie/benh/', '/vi/benh/']]
        disease_links = list(set(disease_links))
        self.logger.info(f"VinmecSpider: Tìm thấy {len(disease_links)} liên kết bệnh độc nhất trên trang này")
        for link in disease_links:
            absolute_url = response.urljoin(link)
            if absolute_url not in self.parsed_urls:
                self.parsed_urls.add(absolute_url)
                yield scrapy.Request(absolute_url, callback=self.parse_disease_page, headers={'Referer': response.url})
        # Xử lý phân trang
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
                yield scrapy.Request(next_url, callback=self.parse_list_page, headers={'Referer': response.url})
        # Các liên kết theo bảng chữ cái và danh mục
        selectors = [
            (['.vm-az-list a::attr(href)', '.block-az-list a::attr(href)', '.alphabet-navigation a::attr(href)', '.az-index a::attr(href)'], self.parse_list_page),
            (['.category-list a::attr(href)', '.vm-category a::attr(href)', '.menu-item a[href*="/benh/"]::attr(href)', '.navigation a[href*="/benh/"]::attr(href)'], self.parse_list_page),
        ]
        for selector_list, callback in selectors:
            links = []
            for selector in selector_list:
                links.extend(response.css(selector).getall())
            if links:
                for link in set(links):
                    absolute_url = response.urljoin(link)
                    if absolute_url not in self.parsed_urls:
                        self.parsed_urls.add(absolute_url)
                        yield scrapy.Request(absolute_url, callback=callback, headers={'Referer': response.url})

    def parse_disease_page(self, response):
        self.disease_count += 1
        self.logger.info(f"VinmecSpider: Phân tích trang bệnh [{self.disease_count}]: {response.url}")
        
        # --- Lấy tên bệnh ---
        disease_name = None
        h1_text = response.css('h1::text').get()
        if h1_text and h1_text.strip() and "Content not available" not in h1_text:
            disease_name = h1_text.strip()
        if not disease_name:
            title_text = response.css('.article-title::text, .page-title::text, .section-heading::text, .title::text').get()
            if title_text and title_text.strip() and "Content not available" not in title_text:
                disease_name = title_text.strip()
        if not disease_name:
            meta_title = response.css('meta[property="og:title"]::attr(content), title::text').get()
            if meta_title and meta_title.strip():
                disease_name = re.sub(r'\s*\|\s*Vinmec.*$', '', meta_title.strip())
        if not disease_name or disease_name.lower() in ["content not available", ""]:
            disease_slug = response.url.split('/')[-1]
            parts = re.sub(r'-\d+$', '', disease_slug).split('-')
            disease_name = ' '.join(parts).title()
        if disease_name.lower() in ['content not available', '']:
            disease_name = "Unknown Disease"
        
        # Nếu tên chứa dấu ":" chỉ lấy phần trước dấu ":" để có tên ngắn gọn
        disease_name = disease_name.strip()
        if ":" in disease_name:
            disease_name = disease_name.split(":", 1)[0].strip()
        self.logger.info(f"Extracted disease name: {disease_name}")
        
        # --- Trích xuất nội dung HTML chính ---
        content_html = ''
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
        if not content_html:
            content_html = response.css('body').get() or ''

        # Hàm làm sạch văn bản
        def clean_text(text):
            unwanted_phrases = [
                "Unfortunately, the content on this page is not available",
                "Please press continue to read the content in Vietnamese",
                "Thank you for your understanding"
            ]
            for phrase in unwanted_phrases:
                text = text.replace(phrase, "")
            return text.strip()

        # --- Định nghĩa các trường cần trích xuất ---
        section_patterns = {
            'description': r'(?:<h2[^>]*>|<h3[^>]*>|<strong[^>]*>)[^<]*?(?:giới thiệu|tổng quan|mô tả|khái quát)[^<]*?(?:</h2>|</h3>|</strong>)(.*?)(?:<h2|<h3|<strong)',
            'symptoms': r'(?:<h2[^>]*>|<h3[^>]*>|<strong[^>]*>)[^<]*?(?:triệu chứng|biểu hiện|dấu hiệu)[^<]*?(?:</h2>|</h3>|</strong>)(.*?)(?:<h2|<h3|<strong)',
            'causes': r'(?:<h2[^>]*>|<h3[^>]*>|<strong[^>]*>)[^<]*?(?:nguyên nhân)[^<]*?(?:</h2>|</h3>|</strong>)(.*?)(?:<h2|<h3|<strong)',
            'risk_factors': r'(?:<h2[^>]*>|<h3[^>]*>|<strong[^>]*>)[^<]*?(?:yếu tố nguy cơ|nguy cơ)[^<]*?(?:</h2>|</h3>|</strong>)(.*?)(?:<h2|<h3|<strong)',
            'diagnosis': r'(?:<h2[^>]*>|<h3[^>]*>|<strong[^>]*>)[^<]*?(?:chẩn đoán)[^<]*?(?:</h2>|</h3>|</strong>)(.*?)(?:<h2|<h3|<strong)',
            'treatment': r'(?:<h2[^>]*>|<h3[^>]*>|<strong[^>]*>)[^<]*?(?:điều trị|phương pháp điều trị|cách điều trị)[^<]*?(?:</h2>|</h3>|</strong>)(.*?)(?:<h2|<h3|<strong)',
            'prevention': r'(?:<h2[^>]*>|<h3[^>]*>|<strong[^>]*>)[^<]*?(?:phòng ngừa|cách phòng)[^<]*?(?:</h2>|</h3>|</strong>)(.*?)(?:<h2|<h3|<strong)',
        }
        
        fallback_section_selectors = {
            'description': ['p:first-of-type', '.introduction', '.summary'],
            'symptoms': ['h2:contains("Triệu chứng") + *', 'h3:contains("Triệu chứng") + *'],
            'causes': ['h2:contains("Nguyên nhân") + *', 'h3:contains("Nguyên nhân") + *'],
            'risk_factors': ['h2:contains("Yếu tố nguy cơ") + *', 'h3:contains("Yếu tố nguy cơ") + *'],
            'diagnosis': ['h2:contains("Chẩn đoán") + *', 'h3:contains("Chẩn đoán") + *'],
            'treatment': ['h2:contains("Điều trị") + *', 'h3:contains("Điều trị") + *'],
            'prevention': ['h2:contains("Phòng ngừa") + *', 'h3:contains("Phòng ngừa") + *'],
        }
        
        sections = {}
        for field, pattern in section_patterns.items():
            matches = re.search(pattern, content_html, re.DOTALL | re.IGNORECASE)
            if matches:
                field_html = matches.group(1)
                list_items = re.findall(r'<li[^>]*>(.*?)</li>', field_html, re.DOTALL)
                if list_items:
                    cleaned_items = []
                    for li in list_items:
                        li_clean = re.sub(r'<[^>]+>', ' ', li)
                        li_clean = re.sub(r'\s+', ' ', li_clean).strip()
                        if li_clean:
                            cleaned_items.append(clean_text(li_clean))
                    if cleaned_items:
                        sections[field] = cleaned_items
                else:
                    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', field_html, re.DOTALL)
                    if paragraphs:
                        cleaned_paras = []
                        for para in paragraphs:
                            para_clean = re.sub(r'<[^>]+>', ' ', para)
                            para_clean = re.sub(r'\s+', ' ', para_clean).strip()
                            if para_clean:
                                cleaned_paras.append(clean_text(para_clean))
                        if cleaned_paras:
                            sections[field] = cleaned_paras
                    else:
                        field_clean = re.sub(r'<[^>]+>', ' ', field_html)
                        field_clean = re.sub(r'\s+', ' ', field_clean).strip()
                        if field_clean:
                            sections[field] = [clean_text(field_clean)]
        
        # Fallback: Nếu regex không bắt được, sử dụng fallback selectors
        for field, selectors in fallback_section_selectors.items():
            if field not in sections:
                for sel in selectors:
                    sel_content = response.css(sel)
                    if sel_content:
                        texts = sel_content.css('::text').getall()
                        if texts:
                            combined = ' '.join([clean_text(t) for t in texts if t.strip()])
                            if combined:
                                sections[field] = [combined]
                                break
        
        # Nếu description vẫn không thu được, lấy vài đoạn <p> đầu trang
        if 'description' not in sections:
            first_paragraphs = response.css('p::text').getall()[:3]
            if first_paragraphs:
                combined = " ".join([clean_text(p) for p in first_paragraphs if p.strip()])
                if combined:
                    sections['description'] = [combined]
                    
        videos = response.css('iframe::attr(src)').getall()
        
        # --- Xây dựng item hoàn chỉnh ---
        item = {
            'id': str(uuid.uuid4()),
            'source': 'vinmec',
            'url': response.url,
            'name': disease_name,
            'description': sections.get('description', [f"Thông tin bệnh {disease_name}"]),
            'symptoms': sections.get('symptoms', []),
            'causes': sections.get('causes', []),
            'risk_factors': sections.get('risk_factors', []),
            'diagnosis': sections.get('diagnosis', []),
            'treatment': sections.get('treatment', []),
            'prevention': sections.get('prevention', []),
            'images': [],
            'videos': videos,
            'extracted_at': response.headers.get('Date').decode("utf-8") if response.headers.get('Date') else None,
            'metadata': {}
        }
        
        self.logger.info(f"VinmecSpider: Đã thu thập dữ liệu cho bệnh: {item['name']}")
        yield item

    def closed(self, reason):
        self.logger.info(f"VinmecSpider: Tổng cộng cào được {self.disease_count} bệnh và {len(self.parsed_urls)} URL")
