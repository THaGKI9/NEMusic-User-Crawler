# Scrapy settings for nemusic project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'nemusic'

SPIDER_MODULES = ['nemusic.spiders']
NEWSPIDER_MODULE = 'nemusic.spiders'
USER_AGENT = 'nemusic-hunter/1.0'
ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = 32
DOWNLOAD_DELAY = .5
COOKIES_ENABLED = False


# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
# ITEM_PIPELINES = {
#     'nemusic.pipelines.NemusicPipeline': 300,
# }
