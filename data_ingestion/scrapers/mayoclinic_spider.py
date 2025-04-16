import scrapy
import string
import re
from urllib.parse import urljoin

class ImprovedMayoClinicSpider(scrapy.Spider):
    name = "mayo"
    allowed_domains = ["mayoclinic.org"]

    def start_requests(self):
        """Tạo request đầu tiên cho mỗi chữ cái (A-Z)"""
        self.logger.info("MayoClinicSpider: Crawling disease list from Mayo Clinic")
        # Uncomment dòng bên dưới để crawl tất cả các chữ cái
        # for letter in string.ascii_uppercase:
        for letter in ["A"]:  # Demo version chỉ crawl bệnh bắt đầu bằng chữ A
            url = f"https://www.mayoclinic.org/diseases-conditions/index?letter={letter}"
            self.logger.info(f"Starting to crawl diseases beginning with: {letter}")
            yield scrapy.Request(url, callback=self.parse_disease_list)

    def parse_disease_list(self, response):
        """Xử lý trang danh sách bệnh theo chữ cái"""
        letter = response.url.split("letter=")[1] if "letter=" in response.url else "Unknown"
        self.logger.info(f"Processing disease list beginning with letter {letter}: {response.url}")
        
        disease_links = response.css('.cmp-list--alphabetical li a::attr(href)').getall()

        if not disease_links:
            self.logger.info("No disease links found with primary selector. Trying alternative selectors.")
            alternative_selectors = [
                'ul.alphabetical-index li a::attr(href)',
                'div.index li a::attr(href)',
                '.index a::attr(href)',
                'ul.index li a::attr(href)',
                'ul li a::attr(href)'
            ]
            for selector in alternative_selectors:
                disease_links = response.css(selector).getall()
                if disease_links:
                    self.logger.info(f"Found links with alternative selector: {selector}")
                    break

        disease_links = [link for link in disease_links if '/diseases-conditions/' in link and '/index' not in link]
        self.logger.info(f"Found {len(disease_links)} diseases beginning with letter {letter}")

        disease_links = disease_links[:3]

        for link in disease_links:
            base_url = re.sub(r'/(symptoms-causes|diagnosis-treatment)/.*$', '', link)
            if '/syc-' in link or '/drc-' in link:
                base_url = link.split('/syc-')[0] if '/syc-' in link else link.split('/drc-')[0]

            full_url = response.urljoin(base_url)
            yield scrapy.Request(full_url, callback=self.parse_main_disease_page)

            disease_name = base_url.split('/')[-1]

            if 'symptoms-causes' in link:
                full_symptoms_url = response.urljoin(link)
                yield scrapy.Request(full_symptoms_url, callback=self.parse_symptoms_causes_page)
            else:
                symptoms_url = f"{base_url}/symptoms-causes/syc-"
                full_symptoms_url = response.urljoin(symptoms_url)
                yield scrapy.Request(full_symptoms_url, callback=self.parse_symptoms_causes_page)
            
            if 'diagnosis-treatment' in link:
                full_treatment_url = response.urljoin(link)
                yield scrapy.Request(full_treatment_url, callback=self.parse_diagnosis_treatment_page)
            else:
                treatment_url = f"{base_url}/diagnosis-treatment/drc-"
                full_treatment_url = response.urljoin(treatment_url)
                yield scrapy.Request(full_treatment_url, callback=self.parse_diagnosis_treatment_page)

    def parse_main_disease_page(self, response):
        """Xử lý trang chính của bệnh và theo dõi các link symptoms-causes và diagnosis-treatment"""
        disease_name = self.extract_disease_name(response)
        self.logger.info(f"Processing main page for disease: {disease_name}")

        symptoms_causes_link = response.css('a[href*="symptoms-causes"]::attr(href)').get()
        diagnosis_treatment_link = response.css('a[href*="diagnosis-treatment"]::attr(href)').get()

        if not symptoms_causes_link:
            symptoms_causes_link = response.xpath('//a[contains(@href, "symptoms-causes")]/@href').get()
        if not diagnosis_treatment_link:
            diagnosis_treatment_link = response.xpath('//a[contains(@href, "diagnosis-treatment")]/@href').get()

        self.logger.info(f"Found symptoms-causes link: {symptoms_causes_link}")
        self.logger.info(f"Found diagnosis-treatment link: {diagnosis_treatment_link}")

        if symptoms_causes_link:
            full_url = response.urljoin(symptoms_causes_link)
            yield scrapy.Request(full_url, callback=self.parse_symptoms_causes_page)
        if diagnosis_treatment_link:
            full_url = response.urljoin(diagnosis_treatment_link)
            yield scrapy.Request(full_url, callback=self.parse_diagnosis_treatment_page)

        if not symptoms_causes_link and not diagnosis_treatment_link:
            item = self.extract_all_content_from_page(response, {
                'source': 'mayoclinic',
                'url': response.url,
                'disease_name': disease_name.strip() if disease_name else '',
                'description': self.extract_description(response)
            })
            yield item

    def parse_symptoms_causes_page(self, response):
        """Phân tích trang Symptoms & Causes và chuyển item sang callback diagnosis-treatment để gộp thông tin"""
        disease_name = self.extract_disease_name(response)
        self.logger.info(f"Processing symptoms-causes for disease: {disease_name}")
        
        item = {
            'source': 'mayoclinic',
            'url': response.url,
            'disease_name': disease_name.strip() if disease_name else '',
            'description': self.extract_description(response),
            'symptoms': self.extract_specific_section(response, 'symptoms', ['symptom', 'signs']),
            'causes': self.extract_specific_section(response, 'causes', ['cause', 'etiology']),
            'risk_factors': self.extract_specific_section(response, 'risk factors', ['risk factor', 'risk']),
            'complications': self.extract_specific_section(response, 'complications', ['complication']),
            'prevention': self.extract_specific_section(response, 'prevention', ['prevent', 'avoiding']),
            'images': self.extract_images(response)
        }
        
        self.log_extracted_info(item)
        
        diagnosis_treatment_link = response.css('a[href*="diagnosis-treatment"]::attr(href)').get()
        if not diagnosis_treatment_link:
            diagnosis_treatment_link = response.xpath('//a[contains(@href, "diagnosis-treatment")]/@href').get()
        
        if diagnosis_treatment_link:
            full_url = response.urljoin(diagnosis_treatment_link)
            yield scrapy.Request(full_url, callback=self.parse_diagnosis_treatment_page, meta={'item': item})
        else:
            yield item

    def parse_diagnosis_treatment_page(self, response):
        """Phân tích trang Diagnosis & Treatment và merge thông tin với item có sẵn (nếu có)"""
        disease_name = self.extract_disease_name(response)
        self.logger.info(f"Processing diagnosis-treatment for disease: {disease_name}")
        
        item = response.meta.get('item')
        if not item:
            item = {
                'source': 'mayoclinic',
                'url': response.url,
                'disease_name': disease_name.strip() if disease_name else '',
                'description': self.extract_description(response),
                'images': self.extract_images(response)
            }
        
        treatment_info = {
            'diagnosis': self.extract_specific_section(response, 'diagnosis', ['diagnos', 'tests', 'exam']),
            'treatment': self.extract_specific_section(response, 'treatment', ['treat', 'therap', 'medication', 'surgery']),
            'preparing_for_appointment': self.extract_specific_section(response, 'preparing for your appointment', ['prepar', 'appointment', 'what to expect']),
            'lifestyle_and_home_remedies': self.extract_specific_section(response, 'lifestyle and home remedies', ['lifestyle', 'home remedies', 'self-care']),
            'alternative_medicine': self.extract_specific_section(response, 'alternative medicine', ['alternative', 'complementary', 'natural']),
            'coping_and_support': self.extract_specific_section(response, 'coping and support', ['cop', 'support', 'living with'])
        }
        
        item.update(treatment_info)
        self.log_extracted_info(item)
        
        yield item

    def extract_all_content_from_page(self, response, item):
        """Trích xuất tất cả nội dung có thể từ một trang (khi không có trang con)"""
        self.logger.info(f"Extracting all content from single page: {response.url}")
        
        item['symptoms'] = self.extract_specific_section(response, 'symptoms', ['symptom', 'signs'])
        item['causes'] = self.extract_specific_section(response, 'causes', ['cause', 'etiology'])
        item['risk_factors'] = self.extract_specific_section(response, 'risk factors', ['risk factor', 'risk'])
        item['complications'] = self.extract_specific_section(response, 'complications', ['complication'])
        item['prevention'] = self.extract_specific_section(response, 'prevention', ['prevent', 'avoiding'])
        
        item['diagnosis'] = self.extract_specific_section(response, 'diagnosis', ['diagnos', 'tests', 'exam'])
        item['treatment'] = self.extract_specific_section(response, 'treatment', ['treat', 'therap', 'medication', 'surgery'])
        item['preparing_for_appointment'] = self.extract_specific_section(response, 'preparing for your appointment', ['prepar', 'appointment', 'what to expect'])
        item['lifestyle_and_home_remedies'] = self.extract_specific_section(response, 'lifestyle and home remedies', ['lifestyle', 'home remedies', 'self-care'])
        item['alternative_medicine'] = self.extract_specific_section(response, 'alternative medicine', ['alternative', 'complementary', 'natural'])
        item['coping_and_support'] = self.extract_specific_section(response, 'coping and support', ['cop', 'support', 'living with'])
        
        item['images'] = self.extract_images(response)
        
        return item

    def extract_disease_name(self, response):
        """Lấy tên bệnh từ trang với nhiều selector cải tiến"""
        selectors = [
            'h1::text',
            'h1 .heading-content::text',
            'h1 span::text',
            'header h1::text',
            '.page-header h1::text',
            '.content h1::text'
        ]
        
        for selector in selectors:
            disease_name = response.css(selector).get()
            if disease_name and disease_name.strip():
                return self.clean_text(disease_name)
        
        disease_name = response.xpath('//h1//text()').get()
        return self.clean_text(disease_name) if disease_name else ''

    def extract_description(self, response):
        """
        Lấy phần mô tả (overview) của bệnh với cách tiếp cận cải tiến.
        """
        description_parts = []
        containers = [
            '#main article',
            '.content',
            '.main-content',
            '.article-body',
            '.cmp-text',
            '.overview',
            '#overview'
        ]
        
        container_selected = None
        for container in containers:
            content = response.css(f'{container}')
            if content:
                container_selected = container
                break
        
        if container_selected:
            overview_section = response.xpath('//h2[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "overview")]')
            if overview_section:
                description_parts = self.extract_section_from_heading(overview_section)
            else:
                elements = response.css(f'{container_selected} > *')
                for elem in elements:
                    tag = elem.xpath('local-name(.)').get() or ""
                    if tag.lower() in ['h2', 'h3']:
                        break
                    text = elem.xpath('string(.)').get()
                    text = self.clean_text(text)
                    if text and not self.is_unwanted_content(text):
                        description_parts.append(text)
        
        if not description_parts:
            paragraphs = response.xpath('//p[preceding::h2[1][contains(@id, "overview")] or not(preceding::h2)]')
            for p in paragraphs:
                text = self.clean_text(p.xpath('string(.)').get())
                if text and not self.is_unwanted_content(text):
                    description_parts.append(text)
        
        return ' '.join(description_parts)

    def extract_specific_section(self, response, section_name, keywords):
        """
        Lấy nội dung của một phần mục dựa theo tiêu đề chứa từ khoá.
        """
        section_content = []
        headings = []
        
        for keyword in keywords:
            headings.extend(response.xpath(
                f'//h2[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{keyword.lower()}")]'
            ))
            headings.extend(response.xpath(
                f'//h3[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{keyword.lower()}")]'
            ))
            headings.extend(response.xpath(
                f'//h4[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{keyword.lower()}")]'
            ))
            headings.extend(response.xpath(
                f'//*[contains(@id, "{keyword.lower()}")]'
            ))
            headings.extend(response.xpath(
                f'//*[contains(@class, "{keyword.lower()}")]'
            ))
        
        unique_headings = []
        heading_texts = set()
        for heading in headings:
            heading_text = heading.xpath('string(.)').get()
            if heading_text and heading_text.strip() not in heading_texts:
                heading_texts.add(heading_text.strip())
                unique_headings.append(heading)
        
        for heading in unique_headings:
            heading_text = heading.xpath('string(.)').get()
            if heading_text:
                heading_text = self.clean_text(heading_text)
            content = self.extract_section_from_heading(heading)
            if content:
                if heading_text and not self.is_unwanted_content(heading_text):
                    section_content.append(heading_text)
                section_content.extend(content)
        
        if not section_content:
            if any(keyword in ['treat', 'therap', 'medication', 'surgery'] for keyword in keywords):
                treatment_containers = response.xpath(
                    '//*[contains(@class, "treatment") or contains(@id, "treatment") or contains(@data-content, "treatment")]'
                )
                for container in treatment_containers:
                    texts = container.xpath('.//p/text() | .//li/text()').getall()
                    for text in texts:
                        text = self.clean_text(text)
                        if text and not self.is_unwanted_content(text):
                            section_content.append(text)
        
        return section_content

    def extract_section_from_heading(self, heading):
        """
        Từ một heading đã xác định, lấy tất cả các node theo thứ tự cho đến khi gặp heading mới.
        """
        content_parts = []
        for sibling in heading.xpath('following-sibling::*'):
            tag = sibling.xpath('local-name(.)').get() or ""
            if tag.lower() in ['h2', 'h3', 'h4']:
                break
            if tag.lower() in ['p', 'li', 'div', 'span']:
                text = sibling.xpath('string(.)').get()
                text = self.clean_text(text)
                if text and not self.is_unwanted_content(text):
                    content_parts.append(text)
            elif tag.lower() in ['ul', 'ol']:
                list_items = sibling.xpath('.//li')
                for item in list_items:
                    text = item.xpath('string(.)').get()
                    text = self.clean_text(text)
                    if text and not self.is_unwanted_content(text):
                        content_parts.append(text)
        if not content_parts:
            children = heading.xpath('./following-sibling::*[1]/*')
            for child in children:
                text = child.xpath('string(.)').get()
                text = self.clean_text(text)
                if text and not self.is_unwanted_content(text):
                    content_parts.append(text)
        return content_parts

    def extract_images(self, response):
        """Lấy URL của hình ảnh liên quan đến bệnh"""
        image_selectors = [
            '#main article img::attr(src)',
            '.content img::attr(src)',
            '.article-body img::attr(src)',
            '.cmp-image img::attr(src)',
            '.main-content img::attr(src)',
            '#symptoms-causes img::attr(src)',
            '#diagnosis-treatment img::attr(src)',
            '.treatments img::attr(src)',
            '.symptoms img::attr(src)',
            'img[alt*="disease"]::attr(src)',
            'img[alt*="symptom"]::attr(src)',
            'img[alt*="treatment"]::attr(src)'
        ]
        
        all_images = []
        for selector in image_selectors:
            images = response.css(selector).getall()
            all_images.extend(images)
        
        all_images = list(set(all_images))
        
        processed_images = []
        for img_src in all_images:
            full_url = urljoin(response.url, img_src)
            if not self.is_unwanted_image(full_url):
                processed_images.append(full_url)
        
        return processed_images

    def is_unwanted_content(self, text):
        """Kiểm tra xem text có chứa những nội dung không mong muốn hay không"""
        if not text or text.isspace():
            return True
        
        unwanted_patterns = [
            r'^A Book:',
            r'^Newsletter:',
            r'Mayo Clinic Health Letter',
            r'Mayo Clinic Family Health Book',
            r'^Share$',
            r'^Print$',
            r'^Email$',
            r'Copyright \d+',
            r'All rights reserved',
            r'Privacy Policy',
            r'Terms of use',
            r'Cookie Settings',
            r'Request an appointment',
            r'Appointment',
            r'Newsletter signup',
            r'Facebook',
            r'Twitter',
            r'Instagram',
            r'LinkedIn',
            r'Advertisement'
        ]
        navigation_patterns = [
            r'Symptoms\s*&\s*causes',
            r'Diagnosis\s*&\s*treatment',
            r'Doctors\s*&\s*departments',
            r'Care at',
            r'Mayo Clinic',
            r'Home\s*$',
            r'Skip to content',
            r'Log in to Patient Account',
            r'Request an Appointment'
        ]
        for pattern in unwanted_patterns + navigation_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def is_unwanted_image(self, image_url):
        """Kiểm tra URL của hình ảnh có phải là quảng cáo hoặc icon không"""
        unwanted_patterns = [
            r'advertisement',
            r'icon',
            r'logo',
            r'banner',
            r'btn',
            r'button',
            r'social',
            r'-ad-',
            r'tracking',
            r'share-',
            r'print-',
            r'email-',
            r'sprite',
            r'thumbnail',
            r'placeholder',
            r'avatar',
            r'pixel\.',
            r'badge',
            r'spacer',
            r'blank',
            r'1x1'
        ]
        for pattern in unwanted_patterns:
            if re.search(pattern, image_url, re.IGNORECASE):
                return True
        small_size_patterns = [r'16x16', r'24x24', r'32x32', r'48x48', r'64x64']
        for pattern in small_size_patterns:
            if re.search(pattern, image_url, re.IGNORECASE):
                return True
        return False

    def log_extracted_info(self, item):
        """Ghi log thông tin đã trích xuất để kiểm tra"""
        disease_name = item.get('disease_name', 'Unknown')
        self.logger.info(f"Successfully scraped disease: {disease_name}")
        for key, value in item.items():
            if key not in ['url', 'source']:
                if isinstance(value, list):
                    count = len(value)
                    examples = value[:2]
                    if count > 0:
                        examples_text = '; '.join(examples)
                        if len(examples_text) > 50:
                            examples_text = examples_text[:50] + '...'
                        self.logger.info(f"  {key}: {count} items. Examples: {examples_text}")
                    else:
                        self.logger.info(f"  {key}: {count} items")
                else:
                    preview = value[:50] + "..." if value and len(value) > 50 else value
                    self.logger.info(f"  {key}: {preview}")

    def clean_text(self, text):
        """
        Hàm xử lý text loại bỏ các ký tự thừa như "\n", "\t" và nhiều khoảng trắng liên tiếp.
        """
        if text:
            return re.sub(r'\s+', ' ', text).strip()
        return ""
