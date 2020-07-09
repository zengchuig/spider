# -*- coding: utf-8 -*-
import scrapy, re, json, time
from JingjigcSpider.items import ArticleItem
from JingjigcSpider.spiders.utils import tool



class HistoryArticleSpider(scrapy.Spider):
    name = 'history_article'
    # allowed_domains = ['app.eeo.com.cn','www.eeo.com.cn']

    # start_urls = ['http://app.eeo.com.cn/']
    def __init__(self, *args, **kwargs):
        self.tools = tool()

    def start_requests(self):
        self.meta = {
            'use_proxy': True,
        }
        self.headers = {
        'User-Agent':
        'Dalvik/2.1.0 (Linux; U; Android 5.1.1; OPPO R9 Plustm A Build/LMY47V)',
        # 'Host': 'app.eeo.com.cn',
        }
        url='http://app.eeo.com.cn/api/app/appCall.php'
        for i in range(1,1751):  #1751
            payload = {
                'jsonParam':
                ' {"map":{"nowPage":"%d","pageShow":"20","sessionId":"","token":"ZphobG9ulpNplmRkaJpmaGtplW+Wo6XIy6DCZJZibWlvxWucbG3Lk5mVaWdnmWZrlpo=","userId":"321929","belongTopicUuid":"3626"},"opetype":"indexPage"}'%i
            }
            yield scrapy.FormRequest(url=url,
                                     headers=self.headers,
                                     formdata=payload,
                                     meta=self.meta,
                                     callback=self.parse)
      
    def parse(self, response):

        data = json.loads(response.text)
        for i in data['newsList']:
            # print(str(i))
            for b in i:
                article_item=ArticleItem()
                article_item['medium_id'] = 1583720635008000
                article_item['medium_name'] = '经济观察报'
                article_item['mp_account_id'] = 1591621839906000
                article_item['mp_account_name'] = '经济观察报'
                article_item['mp_type_id'] = 11
                article_item['mp_type_name'] = '其他'
                article_item['mp_article_id'] = 'jingjigc' + str(b['newsUuid'])
                article_item['title'] = b['newstitle']
                article_item['cover_img'] = self.tools.rebuild_src(
                    b['newsPic'])
                article_item['origin_url'] = b['newsDetailUrl']
                self.meta['article_item']=article_item
                yield scrapy.Request(article_item['origin_url'],
                                     headers=self.headers,
                                     callback=self.parse1,
                                     meta=self.meta)

    def parse1(self, response):
        article_item=response.meta['article_item']
        content = response.xpath(  #article_item['content']
            "//div[@class='t-bottom content-center']/div").extract_first()
        article_item['content'] = self.tools.get_content(content)
        time1 = response.xpath(
            "//span[@class='xc-time']/text()").extract_first()
        time1 = time1[-5:]
        published_at = re.search('com.cn/(.*)/',
                                 article_item['origin_url']).group(1)
        published_at = published_at[:4] + '-' + published_at[
            -4:-2] + '-' + published_at[-2:] + ' ' + time1
        timeArray = time.strptime(published_at, "%Y-%m-%d %H:%M")
        article_item['published_at'] = int(time.mktime(timeArray))
        article_item['read_count'] = 0
        article_item['like_count'] = 0
        article_item['share_count'] = 0
        article_item['comment_count'] = 0
        article_item['is_free'] = 1
        reporter_name_list = response.xpath(
            "//span[@id='space_zuozhe']/text()").extract()
        article_item['reporter_source'] = ','.join(reporter_name_list)
        article_item['reporter_name_list']=[]
        for name in reporter_name_list:
            for i in name.split():
                if self.tools.check_name(i):
                    article_item['reporter_name_list'].append(i)
                    article_item['ori_medium_name']='经济观察报'
                else:
                    article_item['ori_medium_name']=i
        yield article_item
    

