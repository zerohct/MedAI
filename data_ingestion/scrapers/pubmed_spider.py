import scrapy

class PubMedSpider(scrapy.Spider):
    name = "pubmed"
    allowed_domains = ["pubmed.ncbi.nlm.nih.gov"]
    
    def __init__(self, search_term="fever", *args, **kwargs):
        super(PubMedSpider, self).__init__(*args, **kwargs)
        self.search_term = search_term
        self.start_urls = [f"https://pubmed.ncbi.nlm.nih.gov/?term={search_term}"]
    
    def parse(self, response):
        self.logger.info(f"PubMedSpider: Đang cào danh sách bài báo từ PubMed với từ khóa: {self.search_term}")
        
        # Extract articles from the current page
        articles = response.css("article.full-docsum")
        for article in articles:
            title = article.css("a.docsum-title::text").get()
            if title:
                title = title.strip()
            else:
                title = "Unknown Title"
                
            link = article.css("a.docsum-title::attr(href)").get()
            self.logger.info(f"PubMedSpider: Tìm thấy bài báo: {title}")
            
            if link:
                yield response.follow(link, self.parse_article)
        
        # Correct way to find the next page link
        # In PubMed, the next page button is in format like "?term=fever&page=2"
        current_page = response.url.split("page=")
        if len(current_page) > 1:
            current_page_num = int(current_page[1])
            next_page_num = current_page_num + 1
        else:
            next_page_num = 2
        
        # Based on looking at the URL in the screenshot
        base_search = response.url.split("&page=")[0] if "&page=" in response.url else response.url
        next_page_url = f"{base_search}&page={next_page_num}"
        
        # Check if there's a next page by looking for the "Next" button
        next_button = response.css('a.next-page, button.next-page-btn')
        if next_button:
            self.logger.info(f"PubMedSpider: Chuyển sang trang tiếp theo: {next_page_url}")
            yield response.follow(next_page_url, self.parse)
    
    def parse_article(self, response):
        # Extract detailed information from the article page
        title = response.css('h1.heading-title::text').get(default='').strip()
        
        # Handle abstract text that might be in different elements
        abstract_parts = response.css('div.abstract-content p::text, div.abstract p::text').getall()
        abstract = " ".join([part.strip() for part in abstract_parts if part and part.strip()]).strip()
        
        # Get authors with better handling of different author formats
        authors = []
        author_elements = response.css('div.authors-list span.authors-list-item, span.author-name')
        for author in author_elements:
            author_name = author.css('a::text, span::text').get()
            if author_name:
                authors.append(author_name.strip())
        
        # Get publication date
        pub_date = response.css('span.cit::text').get(default='').strip()
        
        # Get keywords/MeSH terms
        keywords = response.css('button.keyword-item-button::text').getall()
        keywords = [k.strip() for k in keywords if k and k.strip()]
        
        item = {
            'source': 'pubmed',
            'url': response.url,
            'title': title,
            'abstract': abstract,
            'authors': authors,
            'publication_date': pub_date,
            'keywords': keywords,
            'search_term': self.search_term 
        }
        
        self.logger.info(f"PubMedSpider: Đã cào xong bài báo: {item['title']}")
        yield item