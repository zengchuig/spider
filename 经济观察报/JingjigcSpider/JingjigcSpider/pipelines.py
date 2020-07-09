# -*- coding: utf-8 -*-

import requests
import json
from pprint import pprint

class JingjigcspiderPipeline(object):
    def process_item(self, item, spider):
        # 保存到tablestore
        api_base_url = spider.settings['API_BASE_URL']
        url = f'{api_base_url}/article'
        col = dict(item)
        headers = {
            'Content-Type': 'application/json',
        }
        pprint(dict(item))
        r = requests.post(url, data=json.dumps(col), headers=headers)
        print(r.text)
        print(f'媒体: {col["medium_name"]} , 标题 {col["title"]}')
        return item




