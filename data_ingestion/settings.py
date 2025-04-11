# Cài đặt cơ bản cho Scrapy
BOT_NAME = 'MEDAI'

SPIDER_MODULES = ['data_ingestion.scrapers']
NEWSPIDER_MODULE = 'data_ingestion.scrapers'

# Tuân theo robots.txt
ROBOTSTXT_OBEY = True

# Pipeline để lưu dữ liệu vào hệ thống 
ITEM_PIPELINES = {
    'data_ingestion.pipelines.SaveItemPipeline': 300,
}

# Cấu hình log hiển thị tiến độ
LOG_LEVEL = 'INFO'
