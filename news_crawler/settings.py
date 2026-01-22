# Scrapy settings for the news_crawler project
#
# This file contains settings for core Scrapy functionality,
# Playwright integration, concurrency, error handling, and AutoThrottle.

BOT_NAME = "news_crawler"

SPIDER_MODULES = ["news_crawler.spiders"]
NEWSPIDER_MODULE = "news_crawler.spiders"

# --- CORE PROJECT SETTINGS ---

# USER_AGENT: Defines a modern browser identity to prevent simple bot detection
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

# Disable robots.txt obedience for broader crawling capability (Standard for news aggregation)
ROBOTSTXT_OBEY = False

# --- PLAYWRIGHT INTEGRATION SETTINGS ---

# Enables the Scrapy-Playwright Download Handler for rendering JavaScript-heavy content
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

# Defines the reactor required for asynchronous operations (mandatory for Playwright/Asyncio)
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Browser settings: Chromium is the most stable engine for headless scraping
PLAYWRIGHT_BROWSER_TYPE = "chromium"

# Robustness: Increased timeout to handle slow Greek news servers and complex ads
# 🛠️ STABILITY FIX: We set this to 90s to give slow pages enough time to render
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 90000

PLAYWRIGHT_LAUNCH_OPTIONS = {
    # Headless mode is enabled for maximum server performance
    "headless": True,
}

# --- ERROR HANDLING & RETRY LOGIC ---

# Enable Scrapy's built-in retry middleware to handle intermittent network failures
RETRY_ENABLED = True
RETRY_TIMES = 3  # Increased retries for better fault tolerance
# Handle specific status codes often associated with server load or anti-bot measures
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# --- CONCURRENCY & THROTTLING (STABILITY OPTIMIZATION) ---

# 🛠️ STABILITY FIX: Reduced global concurrency per worker.
# Since we run 4 parallel workers in concurrent_runner.py, total concurrency will be 4 * 8 = 32.
# This is much safer for a standard internet connection and CPU.
CONCURRENT_REQUESTS = 8

# Limits simultaneous requests per domain. Essential to avoid "net::ERR_NETWORK_CHANGED"
CONCURRENT_REQUESTS_PER_DOMAIN = 2
CONCURRENT_REQUESTS_PER_IP = 0
ITEM_PIPELINES = {
    'news_crawler.pipelines.MySQLPipeline': 300,
    'news_crawler.pipelines.CustomJsonPipeline': 400,
}

# Enable and configure the AutoThrottle extension for dynamic delay management
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3      # Increased initial delay for "polite" crawling
AUTOTHROTTLE_MAX_DELAY = 15       # Increased max delay to handle server pressure
# Target 0.5 requests per second per domain (Lowering this makes the crawl slower but 100% stable)
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5

# --- PIPELINE & OUTPUT SETTINGS ---

# Enable the CustomJsonPipeline to structure and save scraped data into .jsonl files
# ITEM_PIPELINES = {
#    'news_crawler.pipelines.CustomJsonPipeline': 300,
# }

# Export encoding standard for correct Greek character representation
FEED_EXPORT_ENCODING = "utf-8"