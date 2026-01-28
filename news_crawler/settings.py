# Scrapy settings for news_crawler project
# Core configuration for Playwright integration, concurrency, and stability.

BOT_NAME = "news_crawler"

SPIDER_MODULES = ["news_crawler.spiders"]
NEWSPIDER_MODULE = "news_crawler.spiders"

# Use a modern browser string to minimize basic bot detection
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

# Disable robots.txt obedience to maximize news coverage across all sources
ROBOTSTXT_OBEY = False

#PLAYWRIGHT INTEGRATION

# Enable Playwright handlers for full JavaScript rendering (Client-side rendering)
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

# Asyncio reactor is mandatory for Scrapy-Playwright compatibility
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Use Chromium as the default browser engine in headless mode
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
}

# Set navigation timeout to 90s to handle slow servers or heavy assets
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 90000

# --- ERROR HANDLING & RETRY LOGIC ---

RETRY_ENABLED = True
RETRY_TIMES = 3
# Target HTTP codes related to server load or temporary network drops
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# --- PERFORMANCE & STABILITY OPTIMIZATION ---

# Limit global concurrency per worker to 8.
# Total requests will be 32 when running 4 parallel workers.
CONCURRENT_REQUESTS = 8

# Strictly limit to 2 simultaneous requests per domain to avoid network instability and bans
CONCURRENT_REQUESTS_PER_DOMAIN = 2
CONCURRENT_REQUESTS_PER_IP = 0

# Pipeline order: Primary database insertion followed by JSON backup
ITEM_PIPELINES = {
    'news_crawler.pipelines.MySQLPipeline': 300,
    'news_crawler.pipelines.CustomJsonPipeline': 400,
}

# AutoThrottle: Dynamically adjust crawling speed based on server response times
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3      # Initial delay in seconds
AUTOTHROTTLE_MAX_DELAY = 15       # Maximum delay under high load
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5 # Target of 0.5 requests/sec per domain

# Ensure Greek characters are correctly represented in exports
FEED_EXPORT_ENCODING = "utf-8"