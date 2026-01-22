# import json
# import os
#
# class CustomJsonPipeline:
#     def open_spider(self, spider):
#         os.makedirs('results', exist_ok=True)
#         self.files = {}
#
#     def close_spider(self, spider):
#         for file_info in self.files.values():
#             f = file_info['file']
#             f.write('\n]')
#             f.close()
#
#     def process_item(self, item, spider):
#         filename = item.get('filename')
#         if not filename:
#             return item
#
#         if filename not in self.files:
#             file = open(filename, 'w', encoding='utf-8')
#             file.write('[')
#             self.files[filename] = {'file': file, 'first_item': True}
#
#         file_info = self.files[filename]
#
#         item.pop('filename', None)
#
#         if not file_info['first_item']:
#             file_info['file'].write(',\n')
#
#         json.dump(dict(item), file_info['file'], ensure_ascii=False, indent=2)
#
#         file_info['first_item'] = False
#
#         return item
import json
import os
import sys
# Εισαγωγή της συνάρτησης αποθήκευσης από τον database_manager
from .database_manager import save_article


class MySQLPipeline:


    def process_item(self, item, spider):
        if item.get('predicted_label') == 'article' or item.get('is_article_in_category') is True:
            try:
                site_id = item.get('site_id', 1)

                # Κλήση της συνάρτησης save_article για την εγγραφή στη MySQL
                save_article(
                    site_id=site_id,
                    url=item.get('url'),
                    title=item.get('title'),
                    body=item.get('article_body'),
                    image_url=item.get('image_urls')[0] if item.get('image_urls') else None
                )
            except Exception as e:
                # Καταγραφή σφάλματος στα logs του Scrapy αν αποτύχει η σύνδεση
                spider.logger.error(f"MySQL Pipeline Error: {e}")

        return item


class CustomJsonPipeline:
    """
    Το αρχικό σου Pipeline για την αποθήκευση δεδομένων σε αρχεία JSON
    στον φάκελο 'results/'.
    """

    def open_spider(self, spider):
        os.makedirs('results', exist_ok=True)
        self.files = {}

    def close_spider(self, spider):
        for file_info in self.files.values():
            f = file_info['file']
            f.write('\n]')
            f.close()

    def process_item(self, item, spider):
        filename = item.get('filename')
        if not filename:
            return item

        if filename not in self.files:
            file = open(filename, 'w', encoding='utf-8')
            file.write('[')
            self.files[filename] = {'file': file, 'first_item': True}

        file_info = self.files[filename]

        temp_item = dict(item)
        temp_item.pop('filename', None)

        if not file_info['first_item']:
            file_info['file'].write(',\n')

        json.dump(temp_item, file_info['file'], ensure_ascii=False, indent=2)

        file_info['first_item'] = False
        return item