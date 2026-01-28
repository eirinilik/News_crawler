import json
import os
import sys
# Import the database logic from database_manager module
from .database_manager import save_article

class MySQLPipeline:
    """
    Pipeline responsible for filtering items and persisting 'article' data into MySQL.
    It implements the core business logic of storing only valid news content.
    """

    def process_item(self, item, spider):
        # only process items predicted as 'article'
        if item.get('predicted_label') == 'article':
            try:
                # Default site_id to 1 if not provided
                site_id = item.get('site_id', 1)

                # Invoke save_article to handle deduplication (MD5) and DB insertion
                save_article(
                    site_id=site_id,
                    url=item.get('url'),
                    title=item.get('title'),
                    body=item.get('article_body'),
                    image_url=item.get('image_urls')[0] if item.get('image_urls') else None
                )
            except Exception as e:
                # Log errors to Scrapy console for troubleshooting (e.g., connection issues)
                spider.logger.error(f"MySQL Pipeline Error: {e}")

        return item

class CustomJsonPipeline:
    """
    Backup pipeline that stores all crawled items into individual JSON files
    within the 'results/' directory, structured by domain.
    """

    def open_spider(self, spider):
        # Ensure the results directory exists before writing
        os.makedirs('results', exist_ok=True)
        self.files = {}

    def close_spider(self, spider):
        # Finalize and close all open file handles when the spider finishes
        for file_info in self.files.values():
            f = file_info['file']
            f.write('\n]')
            f.close()

    def process_item(self, item, spider):
        # Determine the target filename from the item metadata
        filename = item.get('filename')
        if not filename:
            return item

        # Initialize the file if it hasn't been opened in this session
        if filename not in self.files:
            file = open(filename, 'w', encoding='utf-8')
            file.write('[')
            self.files[filename] = {'file': file, 'first_item': True}

        file_info = self.files[filename]

        # Create a shallow copy of the item to avoid altering the data for other pipelines
        temp_item = dict(item)
        temp_item.pop('filename', None) # Remove 'filename' key from the output JSON

        # Handle JSON comma separation logic
        if not file_info['first_item']:
            file_info['file'].write(',\n')

        # dump the item content to the file with UTF-8 support
        json.dump(temp_item, file_info['file'], ensure_ascii=False, indent=2)

        file_info['first_item'] = False
        return item