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

    # --- Classification Features (Core ML Features) ---
    url_length = scrapy.Field()
    url_depth = scrapy.Field()
    title_length = scrapy.Field()
    text_length = scrapy.Field()
    text_density = scrapy.Field()

    # --- Structural Features ---
    xpath = scrapy.Field()
    source_xpath = scrapy.Field()

    # --- Prediction/Filter Features ---
    has_date_pattern_in_url = scrapy.Field()
    is_category_link = scrapy.Field()

    # --- CRITICAL NEW FEATURE (Checks Trafilatura metadata extraction quality) ---
    has_trafilatura_meta = scrapy.Field()

    # --- Final Classification Output ---
    is_article_in_category = scrapy.Field()

    # NOTE: The fields 'url' and 'title' are intentionally declared once here
    # despite any duplication in feature names from older code versions.