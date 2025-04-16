from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from data_ingestion.scrapers.vinmec_spider import VinmecSpider
from data_ingestion.scrapers.mayoclinic_spider import MayoClinicSpider
from data_ingestion.scrapers.pubmed_spider import PubMedSpider


def run_data_ingestion():
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    
    # Các spider được thêm vào tiến trình - thu thập từ các nguồn khác nhau
    process.crawl(VinmecSpider)
    process.crawl(MayoClinicSpider)
    process.crawl(PubMedSpider)

    
    process.start()  # Block cho đến khi toàn bộ tiến trình kết thúc

def main():
    # Các bước khác trong hệ thống MediInsight AI: ví dụ, tiền xử lý dữ liệu, huấn luyện mô hình, API backend, v.v.
    
    # Bước 1: Thu thập dữ liệu (Data ingestion)
    print("Bắt đầu thu thập dữ liệu từ các nguồn uy tín...")
    run_data_ingestion()
    print("Thu thập dữ liệu hoàn tất.")

    # Giai đoạn 2: Xử lý & chuẩn hóa dữ liệu cho huấn luyện AI
    print("Bắt đầu xử lý dữ liệu...")
    process_all_files()
    print("Xử lý dữ liệu hoàn tất. Dữ liệu được lưu trong thư mục 'processed_data'.")
    # Ví dụ: update database, gọi mô hình huấn luyện,...
    print("Tiếp tục quy trình xử lý và huấn luyện AI...")

if __name__ == '__main__':
    main()
