# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
import base64


# 代理服务器
proxyServer = "http://http-dyn.abuyun.com:9020"

# 代理隧道验证信息
proxyUser = "H414015233FN2BMD"
proxyPass = "0615427E2F13E9B1"
proxyAuth = "Basic " + base64.urlsafe_b64encode(bytes((proxyUser + ":" + proxyPass), "ascii")).decode("utf8")

class JingjigcspiderDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        if request.meta.get('use_proxy'):
            request.meta["proxy"] = proxyServer
            request.headers["Proxy-Authorization"] = proxyAuth
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # url='http://app.eeo.com.cn/api/app/appCall.php'
        # i=1
        # payload = "jsonParam=%7B%22opetype%22%3A%22indexPage%22%2C%22map%22%3A%7B%22pageShow%22%3A%2220%22%2C%22sessionId%22%3A%22%22%2C%22belongTopicUuid%22%3A%223626%22%2C%22userId%22%3A%22%22%2C%22token%22%3A%22Zp9nanFun5RtmWRjZZhkbWhonm6WpaXN0ZnMn8NhmmhryJScbZyYxJuVaWVj%22%2C%22nowPage%22%3A%22{}%22%7D%7D&".format(i)
        # headers = {
        #   'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        #   'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 8.1.0; BKK-AL10 Build/HONORBKK-AL10)',
        #   'Host': 'app.eeo.com.cn',
        #   'Connection': 'Keep-Alive',
        #   'Accept-Encoding': 'gzip',
        #   'Content-Length': '291',
        # }

        # resp=requests.post(url,data=payload,headers=headers)
        # print(resp.text)
        # response.body=resp.content
        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
