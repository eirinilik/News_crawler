import json
import os

class CustomJsonPipeline:
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

        item.pop('filename', None)

        if not file_info['first_item']:
            file_info['file'].write(',\n')

        json.dump(dict(item), file_info['file'], ensure_ascii=False, indent=2)

        file_info['first_item'] = False

        return item
