# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class NemusicItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class NEMusicUserProfile(scrapy.Item):
    uid = scrapy.Field()
    nickname = scrapy.Field()
    gender = scrapy.Field()
    location = scrapy.Field()
    level = scrapy.Field()

    listened_count = scrapy.Field()
    fan_count = scrapy.Field()
    follow_count = scrapy.Field()
    event_count = scrapy.Field()

    create_count = scrapy.Field()
    collect_count = scrapy.Field()

