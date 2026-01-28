import scrapy
from typing import List


class PageItem(scrapy.Item):
    """
    Scrapy Item definition used to hold extracted data and features for classification.
    This structure ensures all data collected by the spider can be saved and processed.
    """
    # --- Identification & Metadata ---
    url = scrapy.Field()
    filename = scrapy.Field()

    # --- Extracted Content ---
    title = scrapy.Field()
    article_body = scrapy.Field()
    image_urls = scrapy.Field()

    url_length = scrapy.Field()
    url_depth = scrapy.Field()
    title_length = scrapy.Field()
    text_length = scrapy.Field()
    text_density = scrapy.Field()

    xpath = scrapy.Field()
    source_xpath = scrapy.Field()

    has_date_pattern_in_url = scrapy.Field()
    is_category_link = scrapy.Field()

    has_trafilatura_meta = scrapy.Field()

    is_article_in_category = scrapy.Field()

