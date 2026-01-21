import scrapy
from urllib.parse import urlparse, urljoin
import json
import re
import os
import sys
from pkgutil import get_data

import trafilatura
from scrapy.selector import Selector
from typing import List, Dict, Any, Pattern
import yaml

SPIDER_DIR = os.path.dirname(os.path.abspath(__file__))

# Identify the project root directory for absolute paths

MANAGER_DIR = os.path.dirname(SPIDER_DIR)
SPIDER_DIR = os.path.dirname(os.path.abspath(__file__))
CRAWLER_DIR = os.path.dirname(SPIDER_DIR)
ROOT_DIR = os.path.dirname(CRAWLER_DIR)               #  Root


# Ensure news_crawler is in the path for imports
if MANAGER_DIR not in sys.path:
    sys.path.append(MANAGER_DIR)


    try:
        from items import PageItem
        import database_manager as db
    except ImportError as e:
        sys.stderr.write(f"failed to import core moduless: {e}\n")
        sys.exit(1)
#clean up
CONFIG_DIR = os.path.join(MANAGER_DIR, "config")
RULES_FILE = os.path.join(CONFIG_DIR, "boilerplate_rules.json")


def  load_cleanup_rules(rules_file):
    #loads and compiles Regex rules per domain from a JSON configuration file
    compiled_rules = {}
    try:
        if not os.path.exists(rules_file):
            return compiled_rules
        with open(rules_file, 'r', encoding='utf-8') as f:
            rules_list = json.load(f)
        for rule in rules_list:
            domain = rule.get('domain')
            patterns = rule.get('patterns')
            if domain and patterns and isinstance(patterns, list):
                compiled_rules[domain] = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in patterns if
                                          isinstance(p, str)]
        return compiled_rules
    except Exception as e:
        sys.stderr.write(f"️ Warnings: Error loading rules from {rules_file}: {e}\n")
        return {}


# Pre-load rules once during module initialization
SITE_REGEX_RULES = load_cleanup_rules(RULES_FILE)


#main class

class UniversalSpider(scrapy.Spider):
    name = "universal_scraper"
    visited_urls = set()
    category_keywords: List[str] = []
    irrelevant_url_keywords: List[str] = []
    sites_to_crawl: List[Dict[str, str]] = []

    # Playwright settings for dynamic content (JavaScript)
    playwright_meta = {
        "playwright": True,
        "playwright_page_goto_kwargs": {"timeout": 60000, "wait_until": "domcontentloaded"},
    }

    def __init__(self, start_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. Load Keywords from YAML
        try:
            yaml_data = get_data('news_crawler', 'general_category_keywords/categories.yml')
            if yaml_data:
                config = yaml.safe_load(yaml_data)
                self.category_keywords = [kw.lower() for cat in config.get('categories', {}).values() for kw in
                                          cat.get('keywords', [])]
                self.category_keywords.extend([kw.lower() for kw in config.get('general_category_keywords', [])])
                self.irrelevant_url_keywords = [kw.lower() for kw in config.get('irrelevant_keywords', [])]
        except Exception:
            pass

        # 2. Retrieve active sources from the database
        sites_data = db.get_active_sites()
        if start_url:
            self.sites_to_crawl = [s for s in sites_data if s.get('start_url').strip() == start_url.strip()]
        else:
            self.sites_to_crawl = sites_data

    def start_requests(self):
        """Starts the crawling process."""
        os.makedirs('results', exist_ok=True)

        # Calculate Allowed Domains for the offsite middleware
        allowed = set()
        for s in self.sites_to_crawl:
            netloc = urlparse(s.get('start_url')).netloc.lower().replace('www.', '')
            if netloc: allowed.add(netloc)
        self.allowed_domains = list(allowed) + [f"www.{d}" for d in allowed]

        for site in self.sites_to_crawl:
            domain = site.get("domain")
            filename = f"results/raw_{domain.replace('.', '_')}.json"

            # Update DB for the visit
            db.update_last_visited(domain)

            yield scrapy.Request(url=site.get("start_url"),
                                 meta={**self.playwright_meta, "depth": 0, "filename": filename, "site_domain": domain},
                                 callback=self.parse_links)

    def parse_links(self, response):
        #lnk extraction and noise filtering.
        if response.meta.get("depth", 0) >= 1: return

        # Targeted selectors for news articles
        link_selectors = ['main a[href]', 'article a[href]', 'a[href*="/article"]', 'a[href*="/story"]',
                          'a[href*="/news"]']
        link_elements = response.css(', '.join(link_selectors)) or response.css('a')

        self.logger.info(f"Found {len(link_elements)} links on    {response.url}")

        seen = set()
        for link_el in link_elements:
            href = link_el.css('::attr(href)').get()
            if not href or href in seen or href.startswith(("javascript", "mailto", "#")): continue
            seen.add(href)
            full_url = urljoin(response.url, href).split('#')[0].split('?')[0].rstrip('/')

            # Domain check
            if urlparse(full_url).netloc.lower().replace('www.', '') not in [d.replace('www.', '') for d in
                                                                             self.allowed_domains]: continue
            if full_url in self.visited_urls: continue
            self.visited_urls.add(full_url)

            # Filtering irrelevant URLs
            if any(kw in full_url.lower() for kw in self.irrelevant_url_keywords): continue

            is_category = any(kw in full_url.lower() for kw in self.category_keywords)
            source_xpath = Selector(text=link_el.get()).xpath('//a/@href').get()

            yield scrapy.Request(full_url,
                                 meta={**self.playwright_meta, "depth": 1, "filename": response.meta.get("filename"),
                                       "is_category_link": is_category, "source_xpath": source_xpath,
                                       "site_domain": response.meta.get("site_domain")}, callback=self.parse_page)

    def clean_text_block(self, paragraphs: List[str]) -> str:
        """Fallback text cleanup if Trafilatura fails."""
        cleaned = []
        for p in paragraphs:
            p_strip = p.strip()
            if not p_strip or len(p_strip) < 20 or re.search(r'[\{\}\;]|\b(var|function|script)\b', p_strip,
                                                             re.I): continue
            cleaned.append(p_strip)
        return "\n\n".join(cleaned)

    def parse_page(self, response):
        """Main content and image extraction."""
        url = response.url

        # Log at DEBUG level for terminal cleanliness
        self.logger.debug(f"📄 Scraping content from: {url}")

        extracted_data = {}
        try:
            extracted_json = trafilatura.extract(response.text, output_format='json', include_comments=False)
            if extracted_json: extracted_data = json.loads(extracted_json)
        except Exception:
            pass

        #  TEXT CLEANUP
        article_body = extracted_data.get('text', '')
        normalized_domain = urlparse(url).netloc.replace('www.', '')
        if normalized_domain in SITE_REGEX_RULES:
            for pattern in SITE_REGEX_RULES[normalized_domain]:
                article_body = pattern.sub('', article_body)

        # Remove generic boilerplates
        article_body = "\n".join([l for l in article_body.split('\n') if
                                  not any(x in l for x in ['Ακολουθήστε μας', 'Follow us', 'Διαβάστε ακόμη'])]).strip()

        if not article_body:
            article_body = self.clean_text_block(
                response.css('article, .post-body, .main-content').xpath('.//text()').getall())

        text_length = len(article_body)
        title = extracted_data.get('title') or response.css('h1::text, title::text').get()
        title_length = len(title) if title else 0

        #  critical logic (Ground Truth for the Random Forest) ---
        is_article_in_category = (not response.meta.get("is_category_link", False)) and (text_length > 150) and (
                title_length > 10)

        #image extraction
        main_image = (
                extracted_data.get('image')
                or response.css("meta[property='og:image']::attr(content)").get()
                or response.css("meta[name='twitter:image']::attr(content)").get()
                or response.css("figure img::attr(src)").get()
                or response.css("article img::attr(src)").get()
        )

        # Convert to absolute URL if relative
        if main_image:
            main_image = response.urljoin(main_image)

        item = PageItem()
        item.update({
            "url": url, "url_length": len(url), "url_depth": url.count("/"),
            "title": title, "title_length": title_length, "text_length": text_length,
            "text_density": text_length / (article_body.count("\n\n") + 1) if text_length else 0,
            "article_body": article_body, "filename": response.meta.get("filename"),
            "is_category_link": response.meta.get("is_category_link", False),
            "is_article_in_category": is_article_in_category,
            "source_xpath": response.meta.get("source_xpath"),
            "xpath": extracted_data.get('xpath') or None,
            "has_date_pattern_in_url": bool(re.search(r"/\d{4}/\d{2}/\d{2}/", url)),
            "image_urls": [main_image] if main_image else [],
            "has_trafilatura_meta": bool(extracted_data.get('date') and extracted_data.get('author'))
        })


        yield item