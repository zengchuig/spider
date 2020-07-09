# coding: utf-8
import json
import logging
import ngender
import re
import random
import requests
import time
from copy import deepcopy

from pprint import pprint
import aliyun_db
import tablestore as ots
# from pyhanlp import HanLP
from distance import levenshtein
from simhash import Simhash, SimhashIndex
from modules import (calc_category, calc_keywords, extract_reporters,
                     clear_all_html, clear_all_html2, get_chinese_name,
                     extract_correspondents)
# from Score_calculater.reporter_score import RepScoreHandler
# from Score_calculater.medium_score import MedScoreHandler
# from Score_calculater.ts_reporter_score import TsRepScoreHandler
# from Score_calculater.ts_medium_score import TsMedScoreHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ArticleHandler(object):
    def __init__(self):
        # self.table_cli = aliyun_db.get_unofficial_product_cli()
        # self.table_ots = aliyun_db.get_official_product_cli()
        self.table_cli = aliyun_db.get_unofficial_test_cli()
        self.table_ots = aliyun_db.get_official_test_cli()
        self.logger = logger

    def write_article(self, raw_article_data):
        """
        Write article into database, steps are as follow:

        1. Query if article exists in table `all_news`.
           If exists, update data in talbe `all_news`, done.
           put data in table `ts_mp_news_data`, done.
           If not exists, goto step 2.

        2. Find similar title in nearlist 10 articles of the same medium
           (Query in table `news`)
           If similar title is found, reserve `news_id` and insert article
           data into table `all_news`, done.
           else write into table `news` to get news_id, goto step 3.

        3. Calc tags, categories, word_count, content begin, content end,
           abstract, reporters list.

        4. For each reporters:
            (1) Query report existance in table `reporters`.
                If exists, increase reporters article number,
                else, add reporters,
            (2) reserver reporter id.

        5. Insert article data inta  table `all_news`.
        Insert article data inta  table `ts_mp_news_data`.

        6. Insert article data into table `news`.

        :param raw_article_data (dict): Article data spider downloads.
            example:
        """
        title = raw_article_data['title']
        if len(title) < 6:
            return
        content = raw_article_data['content']
        content_without_html = clear_all_html(content)
        if len(content) <= 300:
            return
        mp_article_id = raw_article_data['mp_article_id']
        mp_type_id = raw_article_data['mp_type_id']
        medium_id = raw_article_data['medium_id']
        medium_name = raw_article_data['medium_name']
        mp_account_name = raw_article_data['mp_account_name']
        published_at = raw_article_data['published_at']
        reporter_name_list = raw_article_data.get('reporter_name_list', [])
        ori_medium_name = raw_article_data.get('ori_medium_name', '')

        ######################################### Step 1
        # Query article in `all_news`
        article_in_all_news = self.query_article_in_all_news(
            mp_article_id, mp_type_id)
        # If exists, update data in table `all_news`, done.
        if article_in_all_news:
            self.logger.info(
                f'Found Article {raw_article_data["title"]} in `all_news`.')
            news_id = self.update_article_in_all_news(article_in_all_news,
                                                      raw_article_data)
            # Query article in `news`
            article_in_news = self.query_article_in_news(medium_id, news_id)
            if article_in_news:
                self.logger.info(
                    f'Find same article {article_in_news["title"]} in `news`.')
                self.update_article_in_news(article_in_all_news,
                                            raw_article_data, article_in_news,
                                            news_id)
                ts_news_data = self.put_data_in_ts_mp_news_data(
                    article_in_all_news, raw_article_data, article_in_news)
                if mp_type_id != 11:
                    self.update_comment_with_news_id(news_id,
                                                     article_in_all_news['id'],
                                                     mp_article_id)
                # time.sleep(5)
                # ts_rep_handler = TsRepScoreHandler()
                # ts_rep_handler.handler(ts_news_data)
                # ts_med_handler = TsMedScoreHandler()
                # ts_med_handler.handler(ts_news_data)
            return
        self.logger.info(
            f'Article {raw_article_data["title"]} is not found in `all_news`.')

        ######################################### Step 2
        # Find similar article in table `news`.
        similar_article = self.find_similar_article_in_news(
            mp_account_name, medium_id, title, content)
        # If similary article has been found, write article into table `all_news`.
        if similar_article:
            self.logger.info(
                f'Article {similar_article["title"]} is not found in `news`.')
            news_id = similar_article['id']
            prepared_data = self.prepare_data(raw_article_data, news_id)
            pprint(prepared_data)

            # 查看文章转载情况
            new_medium_names, new_medium_ids, reprint_from = self.is_reprint(
                medium_id,
                medium_name,
                ori_medium_name,
                mp_account_name,
                news_id,
                title,
                content,
                mp_type_id,
                published_at,
            )

            # print(medium_name, new_medium_names)
            if medium_name not in new_medium_names:
                # 标注转载他人
                prepared_data['reprinted_status'] = 2
                prepared_data['reprint']['type'] = 2
                if reprint_from:
                    prepared_data['reprint']['list'] = reprint_from
            prepared_data['reprint_from'] = json.dumps(reprint_from,
                                                       ensure_ascii=False)
            prepared_data['reprint'] = json.dumps(prepared_data['reprint'],
                                                  ensure_ascii=False)
            # if [i for i in new_medium_ids if i]:
            #     ind = 0
            #     while True:
            #         new_medium_id = new_medium_ids[ind]
            #         new_medium_name = new_medium_names[ind]
            #         if new_medium_id:
            #             break
            #         else:
            #             ind += 1
            # # 查看记者是否抽取成功
            # other_status = similar_article['other_status']
            # if other_status == 1:
            #     if reporter_name_list:
            #         reporters = self.write_reporters(prepared_data,
            #                                          medium_id,
            #                                          medium_name,
            #                                          news_id,
            #                                          reporter_name_list)
            #         if reporters:
            #             prepared_data['other_status'] = 0
            #         prepared_data['reporters'] = json.dumps(reporters, ensure_ascii=False)
            #     else:
            #         # 解析记者，写入记者表
            #         reporter_name_list = extract_reporters(raw_article_data['content'])
            #         if reporter_name_list:
            #             reporter_name_list = list(filter(None, reporter_name_list))
            #             reporters = self.write_reporters(prepared_data,
            #                                              new_medium_id,
            #                                              new_medium_name,
            #                                              news_id,
            #                                              reporter_name_list)
            #         else:
            #             reporters = []
            #
            #         # If extract reporters success, change `other_status` field.
            #         if reporters:
            #             prepared_data['other_status'] = 0
            #         prepared_data['reporters'] = json.dumps(reporters, ensure_ascii=False)

            # # 解析通讯员
            # correspondent_name_list = extract_correspondents(raw_article_data['content'])
            # if correspondent_name_list:
            #     correspondent_name_list = list(filter(None, correspondent_name_list))
            #     correspondents = self.write_correspondents(prepared_data, news_id,
            #                                                correspondent_name_list)
            # else:
            #     correspondents = []
            #
            # # If extract correspondents success, change `other_status` field.
            # prepared_data['correspondents'] = json.dumps(correspondents, ensure_ascii=False)

            ######################################### Step 5
            all_news_pk, all_news_data = self.save_article_into_all_news(
                prepared_data, news_id)
            all_news_id = all_news_pk['id']
            self.save_data_in_ts_mp_news_data(prepared_data, medium_id,
                                              news_id, all_news_id)

            self.update_article_in_news2(prepared_data, similar_article)
            if mp_type_id != 11:
                self.update_comment_with_news_id(news_id, all_news_id,
                                                 mp_article_id)
            return
        self.logger.info(
            f'Article {raw_article_data["title"]} was not found in `news`.')

        ######################################### Step 3
        news_pk = self.generate_news_id(medium_id)
        news_id = news_pk['id']
        prepared_data = self.prepare_data(raw_article_data, news_id)
        pprint(prepared_data)
        # 查看文章转载情况
        new_medium_names, new_medium_ids, reprint_from = self.is_reprint(
            medium_id,
            medium_name,
            ori_medium_name,
            mp_account_name,
            news_id,
            title,
            content,
            mp_type_id,
            published_at,
        )

        # print(medium_name, new_medium_names)
        if medium_name not in new_medium_names:
            # 标注转载他人
            prepared_data['reprinted_status'] = 2
            prepared_data['reprint']['type'] = 2
            if reprint_from:
                prepared_data['reprint']['list'] = reprint_from
        prepared_data['reprint_from'] = json.dumps(reprint_from,
                                                   ensure_ascii=False)
        prepared_data['reprint'] = json.dumps(prepared_data['reprint'],
                                              ensure_ascii=False)
        ids = []
        names = []
        reporters = []
        for ind in range(len(new_medium_ids)):
            if new_medium_ids[ind]:
                ids.append(new_medium_ids[ind])
                names.append(new_medium_names[ind])
        # 不管原来有没有提取到记者，都提多一次
        extend_reporter_medium_list = ['人民日报', '南方日报']
        # 原来已提取出记者则不需要再提
        extend_reporter_medium_list2 = ['中国基金报']
        if mp_type_id == 11:
            if medium_name in extend_reporter_medium_list:
                extract_reporter_name_list = extract_reporters(
                    raw_article_data['content'])
                if extract_reporter_name_list:
                    reporter_name_list += extract_reporter_name_list
            if medium_name in extend_reporter_medium_list2 and not reporter_name_list:
                extract_reporter_name_list = extract_reporters(
                    raw_article_data['content'])
                if extract_reporter_name_list:
                    reporter_name_list += extract_reporter_name_list
            reporter_name_list = list(
                set(list(filter(None, reporter_name_list))))
            if reporter_name_list and prepared_data['reprinted_status'] == 0:
                reporters = self.write_reporters(prepared_data, medium_id,
                                                 medium_name,
                                                 reporter_name_list)
            else:
                reporters = []
        elif len(ids) == 1:
            # 解析记者，写入记者表
            extract_reporter_name_list = extract_reporters(
                raw_article_data['content'])
            if extract_reporter_name_list:
                extract_reporter_name_list = list(
                    filter(None, extract_reporter_name_list))
                reporters = self.write_reporters(prepared_data, ids[0],
                                                 names[0],
                                                 extract_reporter_name_list)
            else:
                reporters = []

            # If extract reporters success, change `other_status` field.
        if reporters:
            prepared_data['other_status'] = 0
        prepared_data['reporters'] = json.dumps(reporters, ensure_ascii=False)

        # # 解析通讯员
        # correspondent_name_list = extract_correspondents(raw_article_data['content'])
        # if correspondent_name_list:
        #     correspondent_name_list = list(filter(None, correspondent_name_list))
        #     correspondents = self.write_correspondents(prepared_data, news_id,
        #                                                correspondent_name_list)
        # else:
        #     correspondents = []
        #
        # # If extract correspondents success, change `other_status` field.
        # prepared_data['correspondents'] = json.dumps(correspondents, ensure_ascii=False)

        ######################################### Step 5
        all_news_pk, all_news_data = self.save_article_into_all_news(
            prepared_data, news_id)
        all_news_id = all_news_pk['id']
        self.save_data_in_ts_mp_news_data(prepared_data, medium_id, news_id,
                                          all_news_id)
        ######################################### Step 6
        self.save_article_in_news(prepared_data, medium_id, news_id)
        if mp_type_id != 11:
            self.update_comment_with_news_id(news_id, all_news_id,
                                             mp_article_id)
        # time.sleep(5)
        # rep_handler = RepScoreHandler()
        # rep_handler.handler(all_news_data)
        # med_handler = MedScoreHandler()
        # med_handler.handler(all_news_data)

    def save_article_from_news_into_all_news(self, article_in_news,
                                             raw_article_data):
        """
        Save article when we find similar content in table `news`.

        :param article_in_news (dict): Article data find in table `news`.
        :param raw_article_data (dict): Article data recieved from spiders.
        """
        col = deepcopy(article_in_news)
        news_id = article_in_news['id']
        if 'bugs' in col:
            col.pop('bugs')
        col['id'] = None
        col['news_id'] = news_id
        col['like_count'] = raw_article_data['like_count']
        col['comment_count'] = raw_article_data['comment_count']
        col['share_count'] = raw_article_data['share_count']
        col['read_count'] = raw_article_data['read_count']
        col['interact_count'] = raw_article_data[
            'like_count'] + raw_article_data['comment_count']
        col['mp_article_id'] = raw_article_data['mp_article_id']
        col['mp_type_id'] = raw_article_data['mp_type_id']
        col['mp_type_name'] = raw_article_data['mp_type_name']
        col['mp_account_id'] = raw_article_data['mp_account_id']
        col['mp_account_name'] = raw_article_data['mp_account_name']
        col['wx_comment_id'] = raw_article_data['wx_comment_id']
        col['cover_img'] = raw_article_data['cover_img']
        t = int(time.time())
        col['created_at'] = t
        col['updated_at'] = t
        pk = self.table_cli.put_row(table_name='all_news',
                                    pk_list=['medium_id', 'id'],
                                    data=col)
        self.logger.info(f'Put article into `all_news` success {pk}')

    def put_article_into_all_news(self, all_news_data, news_id):
        """
        Put article data into `all_news`.

        :param data (dict): Article data contains all need fields of `all_news`.
        :param news_id (int): News id of table `news`.
        :return (dict): dict contain primary keys and values.
        """
        data = deepcopy(all_news_data)
        data['news_id'] = news_id
        data['id'] = None
        ts = int(time.time())
        data['created_at'] = ts
        data['updated_at'] = ts
        print(data)
        pk = self.table_cli.put_row(table_name='all_news',
                                    pk_list=['medium_id', 'id'],
                                    data=data)
        self.logger.info(f'Put article into `all_news` success {pk}')
        return pk

    def prepare_data(self, data, news_id):
        """
        Calculae tags, categories, word_count, cont_start, cont_end,
        abstract.

        :param data (dict): Raw article data recieved from spiders.
        :param news_id (int): news_id from table `news`.
        """
        col = deepcopy(data)
        tags = self.get_tags(data)
        categories = self.get_categories(data['content'])
        strip_content = clear_all_html(data['content'])
        word_count = len(strip_content)
        col['edition'] = data.get('edition', '')
        col['is_free'] = data.get('is_free', 1)
        col['reporter_source'] = data.get('reporter_source', '')
        col['news_id'] = news_id
        col['tags'] = json.dumps(tags, ensure_ascii=False)
        col['tencent_type1'] = categories['first_level_category']
        col['tencent_type2'] = categories['second_level_category']
        col['news_type_id'] = categories['news_type_id']
        col['news_type_name'] = categories['news_type_name']
        if not data.get('abstract'):
            col['abstract'] = strip_content[:100]
        else:
            col['abstract'] = data['abstract']
        col['word_count'] = word_count
        col['interact_count'] = col['like_count'] + col['comment_count']
        col['reporters'] = json.dumps([], ensure_ascii=False)
        # col['correspondents'] = json.dumps([])
        col['cont_start'] = strip_content[:50]
        col['cont_end'] = strip_content[-25:]
        col['other_status'] = 1
        col['reprinted_status'] = 0
        col['reprint'] = {
            'type': 0,
            'list': [],
        }
        col['created_at'] = int(time.time())
        col['updated_at'] = int(time.time())
        return col

    def get_categories(self, content):
        """
        Get categories.

        :param content str: Article content.
        :return dict: Categories dict.
            {
                "first_level_category": "科技",
                "second_level_category": "创投",
                "news_type_id": 1234,
                "news_type_name": "创投"
            }
        """
        # url = f'http://{API_SERVER}:{API_PORT}/article/categories'
        # payload = {
        #     'content': content,
        # }
        # headers = {
        #     "Content-Type": "application/json",
        # }
        # try:
        #     r = requests.get(url, data=json.dumps(payload), headers=headers, timeout=5)
        #     ret = r.json()['category']
        #     return ret
        # except Exception as e:
        #     print(f'Get category error: {e}')

        first_level_category, second_level_category = calc_category(content)
        news_type_id, news_type_name = self.map_internal_category(
            first_level_category, second_level_category)
        return {
            'first_level_category': first_level_category,
            'second_level_category': second_level_category,
            'news_type_id': news_type_id,
            'news_type_name': news_type_name
        }

    def get_tags(self, data):
        """
        Get article tags, return tags list.

        :param data dict: Article data recieved from spider.
        """
        # url = f'http://{API_SERVER}:{API_PORT}/article/tags'
        # payload = {
        #     'title': data['title'],
        #     'content': data['content'],
        # }
        # self.logger.info(f'get_tags:payload:{payload}')
        # headers = {
        #     "Content-Type": "application/json",
        #     "Accept": "application/json",
        # }
        # try:
        #     r = requests.get(url, data=json.dumps(payload), headers=headers, timeout=60)
        #     tags = r.json()['tags']
        #     return tags
        # except Exception as e:
        #     print(f'Get tags error: {e}')
        #     return []
        return calc_keywords(data['title'], data['content'])

    def map_internal_category(self, tencent_first_level_categroy,
                              second_level_category):
        news_type_id = 0
        news_type_name = '未分类'
        map_dict = {
            '财经': (1, '财经'),
            '彩票': (1, '财经'),
            '科技': (2, '科技'),
            '科学': (2, '科技'),
            '数码': (2, '科技'),
            '房产': (4, '房产'),
            '汽车': (5, '汽车'),
            '社会': (6, '社会'),
            '情感': (6, '社会'),
            '法律': (6, '社会'),
            '体育': (7, '体育'),
            '时政': (8, '时政'),
            '文化': (9, '文娱'),
            '宗教': (9, '文娱'),
            '占卜': (9, '文娱'),
            '娱乐': (9, '文娱'),
            '时尚': (9, '文娱'),
            '动漫': (9, '文娱'),
            '历史': (9, '文娱'),
            '美食': (9, '文娱'),
            '游戏': (9, '文娱'),
            '职场': (9, '文娱'),
            '鸡汤': (9, '文娱'),
            '生活方式': (9, '文娱'),
            '生活百科': (9, '文娱'),
            '天气': (9, '文娱'),
            '宠物': (9, '文娱'),
            '摄影': (9, '文娱'),
            '家居': (9, '文娱'),
            '农林牧副渔': (12, '农业'),
            '旅游': (13, '旅游'),
            '教育': (14, '教育'),
            '育儿': (14, '教育'),
            '移民': (14, '教育'),
            '健康': (19, '健康'),
            '军事': (22, '军事'),
            '国际时政': (28, '国际'),
            '国际社会': (28, '国际'),
        }
        ret = map_dict.get(tencent_first_level_categroy, None)
        if ret is None:
            ret2 = map_dict.get(second_level_category, None)
            if ret2 is None:
                return news_type_id, news_type_name
            return ret2
        return ret

    # def extractor_reporter(self, data):
    #     """
    #     Extract reporters.

    #     :param data [TODO:type]: [TODO:description]
    #     """
    #     url = f'http://{API_SERVER}:{API_PORT}/article/reporters'
    #     payload = {
    #         #'title': data['title'],
    #         'content': data['content'],
    #     }
    #     print(payload)
    #     headers = {
    #         "Content-Type": "application/json",
    #     }
    #     r = requests.get(url, data=json.dumps(payload), headers=headers, timeout=2)
    #     try:
    #         return r.json()['reporters']
    #     except Exception as e:
    #         self.logger.error(f'Get reporters error: {e}')
    #         return []

    def get_features(self, s):
        """
        特征提取
        :param s(str):目标字符串
        :return:
        """
        width = 3
        s = s.lower()
        s = re.sub(r'[^\w]+', '', s)
        return [s[i:i + width] for i in range(max(len(s) - width + 1, 1))]

    def find_similar_article_in_news(self, account_name, medium_id, title,
                                     content):
        """
        Query similar article in news.

        :param medium_id (int): medium_id in
        :param title (str): artice title.
        """
        content = re.sub(
            r'<!--.*?-->|<script.*?/script>|<style.*?/style>|<.*?>', '',
            content)
        content = content.strip()
        must_query = [
            ('term', 'medium_id', medium_id),
        ]
        sort_list = [('created_at', -1)]
        # Query rececent 30 articles of medium with the medium_id.
        result_iter = self.table_cli.query(table_name='news',
                                           must_query_list=must_query,
                                           sort_list=sort_list,
                                           limit=50,
                                           index_name='news_index')
        for query_result in result_iter:
            title_in_db = query_result.get('title', '')
            # simhash title去重
            if levenshtein(title, title_in_db) < 6:
                self.logger.info(
                    f'(title)Found similar article in {account_name}. '
                    f'news_id: {query_result["id"]}')
                return query_result
            else:
                content_in_db = query_result.get('content', '')
                content_in_db = re.sub(
                    r'<!--.*?-->|<script.*?/script>|<style.*?/style>|<.*?>',
                    '', content_in_db)
                content_in_db = content_in_db.strip()
                # simhash content去重
                content_objs = [('1',
                                 Simhash(self.get_features(content_in_db)))]
                content_index = SimhashIndex(content_objs, k=15)
                #  k=int(len(content_in_db) / 50))
                content_hash = Simhash(self.get_features(content))
                if content_index.get_near_dups(content_hash):
                    self.logger.info(
                        f'(content)Found similar article in {account_name}. '
                        f'news_id: {query_result["id"]}')
                    return query_result
        self.logger.info(f'Did not found similar article in {account_name}')
        return

    def query_medium_local(self, medium_id):
        must_query = [
            ('term', 'id', medium_id),
        ]
        result_iter = self.table_cli.query('medium',
                                           must_query_list=must_query,
                                           index_name='medium_index')
        for result in result_iter:
            return result.get('province', ''), result.get('city', '')
        return '', ''

    def query_article_in_all_news(self, mp_article_id, mp_type_id):
        """
        Query article info in table `all_news`.

        :param mp_article_id [int]: media platform article id.
        :return [dict]: If exists, return data dict. else return None.
        """
        must_query = [
            ('term', 'mp_article_id', mp_article_id),
            ('term', 'mp_type_id', mp_type_id),
        ]
        self.logger.info(f'query_article_in_all_news:{must_query}')
        sort_list = [('created_at', -1)]
        result_iter = self.table_cli.query(table_name='all_news',
                                           must_query_list=must_query,
                                           sort_list=sort_list,
                                           index_name='all_news_index')
        for query_result in result_iter:
            self.logger.info(f'查到了同一篇文章，经过for循环')
            return query_result
        return

    def query_article_in_news(self, medium_id, news_id):
        """
        Query article info in table `news`.
        """
        must_query = [
            ('term', 'medium_id', medium_id),
            ('term', 'id', news_id),
        ]
        self.logger.info(f'query_article_in_news:{must_query}')
        sort_list = [('created_at', -1)]
        result_iter = self.table_cli.query(table_name='news',
                                           must_query_list=must_query,
                                           sort_list=sort_list,
                                           index_name='news_index')
        for query_result in result_iter:
            self.logger.info(f'获取到news的文章，经过for循环')
            return query_result
        return

    def update_article_in_news(self, article_in_all_news, raw_article_data,
                               article_in_news, news_id):
        """
        Update article in table `news`.
        """
        news_data = deepcopy(article_in_news)
        news_data['medium_id'] = raw_article_data['medium_id']
        if news_data['medium_id'] == 1583720631765000:
            news_data['content'] = raw_article_data['content']
        news_data['mp_account_id'] = raw_article_data['mp_account_id']
        news_data['is_free'] = raw_article_data['is_free']
        news_data['id'] = news_id
        news_data['read_count'] = news_data.get('read_count', 0)\
                                      + raw_article_data.get('read_count', 0) \
                                      - article_in_all_news.get('read_count', 0)
        news_data['like_count'] = news_data.get('like_count', 0) \
                                      + raw_article_data.get('like_count', 0)\
                                      - article_in_all_news.get('like_count', 0)
        news_data['comment_count'] = news_data.get('comment_count', 0) \
                                         + raw_article_data.get('comment_count', 0) \
                                         - article_in_all_news.get('comment_count', 0)
        news_data['share_count'] = news_data.get('share_count', 0) \
                                       + raw_article_data.get('share_count', 0) \
                                       - article_in_all_news.get('share_count', 0)
        news_data['interact_count'] = news_data['like_count'] + news_data[
            'comment_count']
        if 'mp_type_id' not in news_data.keys():
            news_data['mp_type_id'] = raw_article_data['mp_type_id']
            news_data['mp_type_name'] = raw_article_data['mp_type_name']
        if 'cover_img' not in news_data.keys():
            news_data['cover_img'] = raw_article_data['cover_img']
        news_data['updated_at'] = int(time.time())
        # news_data['created_at'] = int(time.time())
        pk = self.table_cli.update_row(table_name='news',
                                       pk_list=['medium_id', 'id'],
                                       data=news_data)
        self.logger.info(f'Update article in `news`: {pk}')

    def update_article_in_news2(self, prepared_data, article_in_news):
        """
        Update article in table `news`.
        """
        news_data = deepcopy(article_in_news)
        news_data['reporter_source'] = news_data.get(
            'reporter_source', '') if news_data.get('reporter_source',
                                                    '') else prepared_data.get(
                                                        'reporter_source', '')
        # ori_is_free = news_data.get('is_free', 1)
        # if ori_is_free == 0:
        #     news_data['is_free'] = prepared_data['is_free']
        news_data['is_free'] = prepared_data['is_free']
        news_data['mp_account_id'] = prepared_data['mp_account_id']
        news_data['read_count'] = news_data.get(
            'read_count', 0) + prepared_data.get('read_count', 0)
        news_data['like_count'] = news_data.get(
            'like_count', 0) + prepared_data.get('like_count', 0)
        news_data['comment_count'] = news_data.get(
            'comment_count', 0) + prepared_data.get('comment_count', 0)
        news_data['share_count'] = news_data.get(
            'share_count', 0) + prepared_data.get('share_count', 0)
        if 'mp_type_id' not in news_data.keys():
            news_data['mp_type_id'] = prepared_data['mp_type_id']
            news_data['mp_type_name'] = prepared_data['mp_type_name']
        if 'cover_img' not in news_data.keys():
            news_data['cover_img'] = prepared_data['cover_img']
        news_data['other_status'] = prepared_data['other_status']
        if 'reporters' not in news_data.keys():
            news_data['reporters'] = prepared_data['reporters']
        # if 'correspondents' not in news_data.keys():
        #     news_data['correspondents'] = prepared_data['correspondents']
        if 'reprint_from' not in news_data.keys():
            news_data['reprint_from'] = prepared_data['reprint_from']
            news_data['reprint'] = prepared_data['reprint']
            self.logger.info(f'reprint_from: {news_data["reprint_from"]}')
        news_data['updated_at'] = int(time.time())
        # news_data['created_at'] = int(time.time())
        pk = self.table_cli.update_row(table_name='news',
                                       pk_list=['medium_id', 'id'],
                                       data=news_data)
        self.logger.info(f'Update article in `news`: {pk}')

    def save_article_in_news(self, prepared_data, medium_id, news_id):
        """
        Save article in table `news`.

        :param prepared_data [TODO:type]: [TODO:description]
        :param medium_id [TODO:type]: [TODO:description]
        :param news_id [TODO:type]: [TODO:description]
        """
        news_data = deepcopy(prepared_data)
        self.logger.info(f'reprint_from: {news_data["reprint_from"]}')
        discard_keys = [
            'news_id',
            'mp_article_id',
            'wx_comment_id',
            'reporter_name_list',
            'ori_medium_name',
            'reporter_data',
        ]
        for key in discard_keys:
            if key in news_data:
                news_data.pop(key)
        time_now = int(time.time())
        news_data['id'] = news_id
        news_data['medium_id'] = medium_id
        news_data['interact_count'] = news_data['like_count'] + news_data[
            'comment_count']
        news_data['updated_at'] = time_now
        news_data['created_at'] = time_now
        pk = self.table_cli.update_row(table_name='news',
                                       pk_list=['medium_id', 'id'],
                                       data=news_data)
        self.logger.info(f'Save article in `news`: {pk}')
        return pk

    def update_article_in_all_news(self, article_in_all_news, new_data):
        """
        Update attribes of article in `all_news`.

        :param article_in_all_news (dict): article data query from `all_news`.
        :param new_data (dict): columns data dict wait to update.
        """
        # Update old data dict.
        data = deepcopy({**article_in_all_news, **new_data})
        data['read_count'] = new_data.get('read_count',
                                          data.get('read_count', 0))
        data['like_count'] = new_data.get('like_count',
                                          data.get('like_count', 0))
        data['comment_count'] = new_data.get('comment_count',
                                             data.get('comment_count', 0))
        data['share_count'] = new_data.get('share_count',
                                           data.get('share_count', 0))
        data['interact_count'] = data['like_count'] + data['comment_count']
        data['medium_id'] = new_data['medium_id']
        data['updated_at'] = int(time.time())
        # Update table `all_news`.
        pk = self.table_cli.update_row(table_name='all_news',
                                       pk_list=['medium_id', 'id'],
                                       data=data)
        self.logger.info(f'Update article in all news: {pk}')
        return data['news_id']

    def put_data_in_ts_mp_news_data(self, article_in_all_news, new_data,
                                    article_in_news):
        """
        Put data of article in `ts_mp_news_data`.
        """
        # Update old data dict.
        data = deepcopy({**article_in_all_news, **new_data})
        ts_data = dict()
        ts_data['medium_id'] = data['medium_id']
        ts_data['id'] = None
        ts_data['mp_account_id'] = data['mp_account_id']
        ts_data['mp_type_id'] = data['mp_type_id']
        ts_data['all_news_id'] = data['id']
        ts_data['news_id'] = data['news_id']
        ts_data['origin_url'] = data['origin_url']
        ts_data['news_type_id'] = data.get('news_type_id', 0)
        ts_data['news_type_name'] = data.get('news_type_name', '未分类')
        ts_data['read_count'] = data['read_count']
        ts_data['like_count'] = data['like_count']
        ts_data['comment_count'] = data['comment_count']
        ts_data['share_count'] = data['share_count']
        ts_data['interact_count'] = data['like_count'] + data['comment_count']
        ts_data['increment_read_count'] = new_data[
            'read_count'] - article_in_all_news['read_count']
        ts_data['increment_read_count'] = ts_data[
            'increment_read_count'] if ts_data[
                'increment_read_count'] > 0 else 0
        ts_data['increment_like_count'] = new_data[
            'like_count'] - article_in_all_news['like_count']
        ts_data['increment_like_count'] = ts_data[
            'increment_like_count'] if ts_data[
                'increment_like_count'] > 0 else 0
        ts_data['increment_comment_count'] = new_data[
            'comment_count'] - article_in_all_news['comment_count']
        ts_data['increment_comment_count'] = ts_data[
            'increment_comment_count'] if ts_data[
                'increment_comment_count'] > 0 else 0
        ts_data['increment_share_count'] = new_data[
            'share_count'] - article_in_all_news['share_count']
        ts_data['increment_share_count'] = ts_data[
            'increment_share_count'] if ts_data[
                'increment_share_count'] > 0 else 0
        ts_data['increment_interact_count'] = new_data['like_count'] - article_in_all_news['like_count'] \
                                              + new_data['comment_count'] - article_in_all_news['comment_count']
        ts_data['increment_interact_count'] = ts_data[
            'increment_interact_count'] if ts_data[
                'increment_interact_count'] > 0 else 0
        ts_data['reporters'] = article_in_news['reporters']
        ts_data['created_at'] = int(time.time())
        ts_data['updated_at'] = int(time.time())
        # Update table `ts_mp_news_data`.
        pk = self.table_cli.update_row(table_name='ts_mp_news_data',
                                       pk_list=['medium_id', 'id'],
                                       data=ts_data)
        self.logger.info(f'Put data in ts_mp_news_data: {pk}')
        return ts_data

    def save_data_in_ts_mp_news_data(self, prepared_data, medium_id, news_id,
                                     all_news_id):
        """
        Save data of article in `ts_mp_news_data`.
        """
        # Update old data dict.
        data = deepcopy(prepared_data)
        ts_data = dict()
        ts_data['medium_id'] = medium_id
        ts_data['id'] = None
        ts_data['mp_account_id'] = data['mp_account_id']
        ts_data['mp_type_id'] = data['mp_type_id']
        ts_data['all_news_id'] = all_news_id
        ts_data['news_id'] = news_id
        ts_data['origin_url'] = data['origin_url']
        ts_data['news_type_id'] = data['news_type_id']
        ts_data['news_type_name'] = data['news_type_name']
        ts_data['read_count'] = data['read_count']
        ts_data['like_count'] = data['like_count']
        ts_data['comment_count'] = data['comment_count']
        ts_data['share_count'] = data['share_count']
        ts_data['reporters'] = data['reporters']
        ts_data['interact_count'] = data['like_count'] + data['comment_count']
        ts_data['increment_read_count'] = 0
        ts_data['increment_like_count'] = 0
        ts_data['increment_comment_count'] = 0
        ts_data['increment_share_count'] = 0
        ts_data['increment_interact_count'] = 0
        ts_data['created_at'] = int(time.time())
        ts_data['updated_at'] = int(time.time())
        # Update table `ts_mp_news_data`.
        pk = self.table_cli.update_row(table_name='ts_mp_news_data',
                                       pk_list=['medium_id', 'id'],
                                       data=ts_data)
        self.logger.info(f'Save data in ts_mp_news_data: {pk}')

    def save_article_into_all_news(self, prepared_data, news_id):
        """Save article in table `all_news`.
        """

        col = deepcopy(prepared_data)
        discard_keys = [
            'reporter_name_list',
            'ori_medium_name',
            'reporter_data',
        ]
        for key in discard_keys:
            if key in col:
                col.pop(key)
        self.logger.info(f'save all news data:{col}')
        col['id'] = None
        col['news_id'] = news_id
        col['interact_count'] = col['like_count'] + col['comment_count']
        t = int(time.time())
        col['created_at'] = t
        col['updated_at'] = t
        pk = self.table_cli.put_row(table_name='all_news',
                                    pk_list=['medium_id', 'id'],
                                    data=col)
        self.logger.info(f'save article into `all_news` success {pk}')
        return pk, col

    def generate_news_id(self, medium_id):
        """
        Insert empty data into table news to get `news_id`.

        :param medium_id (int): Medium id.
        """
        col = {
            'medium_id': medium_id,
            'id': None,
        }
        pk = self.table_cli.put_row(table_name='news',
                                    pk_list=['medium_id', 'id'],
                                    data=col)
        self.logger.info(f'Generate news id: {pk}')
        return pk

    def find_similar_account(self, account_name):
        """
        查找是否存在该媒体
        :param account_name(str): 媒体号名
        :return:
        """
        must_query = [
            ('term', 'name', account_name),
        ]
        sort_list = [('id', -1)]
        result_iter = self.table_cli.query(table_name='medium',
                                           must_query_list=must_query,
                                           sort_list=sort_list,
                                           index_name='medium_index')
        if not result_iter:
            return
        for medium in result_iter:
            if medium["name"] == account_name:
                self.logger.info(
                    f'find original account_name:{account_name} in medium')
                return medium["id"]
            else:
                return

    def update_reprint_to_in_news(self, similar_article, reprint_to):
        """
        把reprint_to写入news
        :param similar_article(list): 文章list
        :param rt(dict): 被转载
        :return:
        """
        news_data = deepcopy(similar_article)
        news_data['reprint_to'] = json.dumps([reprint_to], ensure_ascii=False)
        reprint = {
            'type': 1,
            'list': json.loads(news_data['reprint_to']),
        }
        news_data['reprint'] = json.dumps(reprint, ensure_ascii=False)
        news_data['updated_at'] = int(time.time())
        news_data['reprinted_status'] = 1
        pk = self.table_cli.update_row(table_name='news',
                                       pk_list=['medium_id', 'id'],
                                       data=news_data)
        self.logger.info(f'Update article in `news`: {pk}')

    def query_word(self, word, keyword_list, n_list):
        if word[1] not in n_list:
            return
        for keyword in keyword_list:
            if keyword in word[0] and len(word[0]) > 2:
                return word[0]
        else:
            return

    # def get_account_name(self, result):
    #     # 目标关键词
    #     keyword_list = [
    #         '报', '时报', '日报', '晚报', '商报', '晨报', '都市报', '新报', '早报', '社', '刊',
    #         '日刊', '周刊', '区报', '快报', '时讯'
    #     ]
    #     n_list = [
    #         'n', 'ni', 'nic', 'nit', 'nt', 'ntc', 'ntcb', 'ntcf', 'ntch',
    #         'nth', 'nto', 'nts', 'ntu', 'nz', 'nnt', 'ns'
    #     ]
    #     account_name = ''
    #     # 规则匹配
    #     for i in range(1, len(result) - 1):
    #         # 当前分词。索引0对应名称，索引1对应词性
    #         word = str(result.get(int(i))).split('/')
    #         if word[1] in ['w', '']:
    #             continue
    #         # 前一个分词
    #         pre_ind = int(i - 1)
    #         pre_word = str(result.get(pre_ind)).split('/')
    #         while True:
    #             if pre_ind == 0 or pre_word[1] not in ['w', '']:
    #                 break
    #             else:
    #                 pre_ind -= 1
    #                 pre_word = str(result.get(pre_ind)).split('/')
    #         # 前两个分词
    #         if int(pre_ind - 1) >= 0:
    #             pre_word_2 = str(result.get(pre_ind - 1)).split('/')
    #         else:
    #             pre_word_2 = [' ', 'w']
    #         # 后一个分词
    #         next_word = str(result.get(int(i + 1))).split('/')
    #         # 后两个分词
    #         if int(i + 2) <= len(result) - 1:
    #             next_word_2 = str(result.get(int(i + 2))).split('/')
    #         else:
    #             next_word_2 = [' ', 'w']
    #         # next_ind = int(i + 1)
    #         # next_word = str(result.get(next_ind)).split('/')
    #         # while True:
    #         #     if next_ind == len(result) or next_word[1] not in ['w']:
    #         #         break
    #         #     else:
    #         #         next_ind += 1
    #         #         next_word = str(result.get(next_ind)).split('/')
    #         # self.logger.info(f'pre_word: {pre_word},word: {word},next_word: {next_word}')
    #         if pre_word[0] in ['来源']:
    #             if self.query_word(word, keyword_list, n_list):
    #                 account_name = word[0]
    #                 self.logger.info(f'account_name：{account_name}')
    #                 return account_name
    #             elif (next_word[0] in keyword_list or next_word[1] in ['nis']
    #                   ) and len(word[0]) > 1 and word[1] not in ['w', '']:
    #                 account_name = word[0] + next_word[0]
    #                 self.logger.info(f'account_name：{account_name}')
    #                 return account_name
    #             elif word[1] in ['ns'] and (next_word_2[0] in keyword_list or next_word_2[1] in ['nis']) \
    #                     and len(next_word[0]) > 1 and next_word[1] not in ['w', '']:
    #                 account_name = word[0] + next_word[0] + next_word_2[0]
    #                 self.logger.info(f'account_name：{account_name}')
    #                 return account_name
    #             elif next_word[1] in [
    #                     'ns'
    #             ] and len(next_word[1]) < 4 and word[0] in ['今日']:
    #                 account_name = word[0] + next_word[0]
    #                 self.logger.info(f'account_name：{account_name}')
    #                 return account_name
    #             elif word[1] in n_list and len(word[0]) >= 2:
    #                 if next_word[1] in n_list:
    #                     account_name = word[0] + next_word[0]
    #                     self.logger.info(f'account_name：{account_name}')
    #                     return account_name
    #                 else:
    #                     account_name = word[0]
    #                     self.logger.info(f'account_name：{account_name}')
    #                     return account_name
    #         if pre_word[0] in ['据', '根据'] and next_word[0] in ['电', '报', '报道']:
    #             if word[1] in n_list and len(word[0]) > 2:
    #                 account_name = word[0]
    #                 self.logger.info(f'account_name：{account_name}')
    #                 return account_name
    #         if next_word[0] in ['电', '报道'] and next_word_2[0] in ['w', '']:
    #             if self.query_word(word, keyword_list, n_list):
    #                 account_name = word[0]
    #                 self.logger.info(f'account_name：{account_name}')
    #                 return account_name
    #             elif (word[0] in keyword_list or word[1] in ['nis']) and len(
    #                     pre_word[0]) > 1 and pre_word[1] not in ['w', '']:
    #                 account_name = pre_word[0] + word[0]
    #                 self.logger.info(f'account_name：{account_name}')
    #                 return account_name
    #             elif pre_word_2[1] in [
    #                     'ns'
    #             ] and (word[0] in keyword_list or word[1] in ['nis']) and len(
    #                     pre_word[0]) > 1 and pre_word[1] not in ['w', '']:
    #                 account_name = pre_word_2[0] + pre_word[0] + word[0]
    #                 self.logger.info(f'account_name：{account_name}')
    #                 return account_name
    #             elif word[1] in [
    #                     'ns'
    #             ] and len(word[1]) < 4 and pre_word[0] in ['今日']:
    #                 account_name = pre_word[0] + word[0]
    #                 self.logger.info(f'account_name：{account_name}')
    #                 return account_name

    # # 直接匹配
    # for i in range(1, len(result) - 1):
    #     # 当前分词。索引0对应名称，索引1对应词性
    #     word = str(result.get(int(i))).split('/')
    #     # 前一个分词
    #     pre_word = str(result.get(int(i - 1))).split('/')
    #     # 后一个分词
    #     next_word = str(result.get(int(i + 1))).split('/')
    #     # self.logger.info(f'pre_word: {pre_word},word: {word},next_word: {next_word}')
    #     n_list = ['n', 'ni', 'nic', 'nit', 'nt', 'nto', 'nz']
    #     if self.query_word(word, keyword_list, n_list):
    #         account_name = word[0]
    #         self.logger.info(f'account_name：{account_name}')
    #         return account_name
    #     elif (next_word[0] in keyword_list or next_word[1] in ['nis']) and len(word[0]) > 1 and word[1] not in [
    #         'w']:
    #         if pre_word[1] in ['ns']:
    #             account_name = pre_word[0] + word[0] + next_word[0]
    #         else:
    #             account_name = word[0] + next_word[0]
    #         self.logger.info(f'account_name：{account_name}')
    #         return account_name
    #     elif word[1] in ['ns'] and len(word[1]) < 4 and pre_word[0] in ['今日']:
    #         account_name = pre_word[0] + word[0]
    #         self.logger.info(f'account_name：{account_name}')
    #         return account_name
    #     # elif word[1] in ['nt', 'nz'] and len(word[0]) > 2:
    #     #     account_name = word[0]
    #     #     break
    # self.logger.info(f'account_name：{account_name}')
    # return account_name

    def query_extract(self, content):
        # content = '三峡晚报融媒体综合人民日报三峡快报'
        keyword_list = [
            '报', '时报', '日报', '晚报', '商报', '晨报', '都市报', '新报', '早报', '社', '刊',
            '日刊', '周刊', '区报', '快报', '时讯'
        ]
        accounts = []
        for keyword in keyword_list:
            if keyword in content:
                results = content.split(keyword, 1)
                accounts.append(results[0] + keyword)
                content = content.replace(results[0] + keyword, '')
        return accounts

    # 全表查找原创文章
    def find_ori_article_in_news(self, title, content, published_at):
        """
        Query similar article in news.

        :param medium_id (int): medium_id in
        :param title (str): artice title.
        """
        content = re.sub(
            r'<!--.*?-->|<script.*?/script>|<style.*?/style>|<.*?>', '',
            content)
        content = content.strip()
        must_query = [
            ('phrase', 'title', title),
        ]
        sort_list = [('published_at', 1)]
        # Query rececent 30 articles of medium with the medium_id.
        result_iter = self.table_cli.query(table_name='news',
                                           must_query_list=must_query,
                                           sort_list=sort_list,
                                           limit=30,
                                           index_name='news_index')
        for query_result in result_iter:
            content_in_db = query_result.get('content', '')
            published_in_db = query_result['published_at']
            # simhash content去重
            content_objs = [('1', Simhash(self.get_features(content_in_db)))]
            content_index = SimhashIndex(content_objs, k=10)
            content_hash = Simhash(self.get_features(content))
            if content_index.get_near_dups(
                    content_hash) and int(published_at) > int(published_in_db):
                self.logger.info(f'Found ori article in news. '
                                 f'news_id: {query_result["id"]}')
                return query_result
        self.logger.info(f'Did not found ori article in news')
        return

    def get_account_name2(self, title, content, published_at,
                          account_name_list):
        # 若标题含有原媒体字眼，则返回原媒体，否则继续
        second_medium_list = [
            '央视新闻',
        ]
        second_medium_dict = {
            '央视新闻': ['央视快评'],
        }
        for key in second_medium_dict:
            for title_str in second_medium_dict[key]:
                if title_str in title:
                    self.logger.info(
                        f'news:{title} is original from medium:{key}')
                    account_name_list.append(key)
        # logger.info(content)
        content_without_html = clear_all_html(content)
        top_content_without_html = content_without_html[:30]
        tail_content_without_html = content_without_html[-100:]
        content_without_html = top_content_without_html + '/n' + tail_content_without_html
        # logger.info(content_without_html)
        pattern_list = [
            # re.compile('据([\u4e00-\u9fa5A-Z]{3,20}?)报道'),
            re.compile(
                r'(?:>|文|文章|新闻)来[ ]?源[丨｜：: /]?(.*?)(?=[<《》）\)，。"“”"]|文 |本文|通讯|编辑|摄影|监制|记者|海报|视频|\u0001$)',
                re.S),
        ]
        top_pattern_list = [
            re.compile(r'据([\u4e00-\u9fa5A-Z]{3,20}?)(?=报道|电，)'),
        ]
        # logger.info(top_content_without_html)
        tail_pattern_list = [
            re.compile(
                r'来[ ]?源[丨｜：: /]?(.{3,20}?)(?=。|，|文 |本文|通讯|编辑|摄影|监制|记者|  |海报|视频|\u0001$)'
                # r'来[ ]?源[丨｜：: /]?([\u4e00-\u9fa5A-Z]{3,20}?)(?=。|，|文 |通讯|编辑|摄影|监制|记者|  |海报|视频|\u0001$)'
            ),
        ]
        # logger.info(tail_content_without_html)
        medium_name_str_list = []
        for pattern in pattern_list:
            medium_name_str_list.extend(re.findall(pattern, content))
        for pattern in top_pattern_list:
            medium_name_str_list.extend(
                re.findall(pattern, top_content_without_html))
        for pattern in tail_pattern_list:
            medium_name_str_list.extend(
                re.findall(pattern, tail_content_without_html))
        # 针对新华社的处理
        for sp_name in ['新华社', '央视新闻']:
            # 首部处理
            if re.findall(sp_name, top_content_without_html):
                medium_name_str_list.append(sp_name)
            # 尾部处理
            sp_str_list = [
                f'{sp_name}[\u4e00-\u9fa5A-Za-z]*?[记作]+?者',
                f'[（\(]+?{sp_name}.*?[）\)]+?',
                f'据{sp_name}',
                # f'{sp_name}电',
                f'综合自{sp_name}',
                f'来自{sp_name}',
                f'[据]?{sp_name}[\u4e00-\u9fa5A-Za-z1-9]*?电',
            ]
            for sp_str in sp_str_list:
                if re.findall(sp_str, tail_content_without_html):
                    medium_name_str_list.append(sp_name)
        # 针对央视处理
        for sp_name in ['央视']:
            # 首部处理
            if re.findall(sp_name, content_without_html) and re.findall(
                    '原[标]?题', content_without_html):
                medium_name_str_list.append(sp_name)
            # 尾部处理
            sp_str_list = [
                f'{sp_name}[\u4e00-\u9fa5A-Za-z]*?[记作]+?者',
            ]
            for sp_str in sp_str_list:
                if re.findall(sp_str, tail_content_without_html):
                    medium_name_str_list.append(sp_name)
        medium_name_str_list = list(set(medium_name_str_list))
        temp_list = medium_name_str_list
        for temp in temp_list:
            extracts = re.findall(r"([\u4e00-\u9fa5]{3,})", temp)
            for extract in extracts:
                extracts.remove(extract)
                if len(extract) > 8:
                    new_extracts = self.query_extract(extract)
                    extracts += new_extracts
                else:
                    extracts.append(extract)
            account_name_list += extracts
        new_account_list = []
        for account_name in list(set(account_name_list)):
            if get_chinese_name(account_name):
                continue
            if account_name[-1] == '等':
                new_account_list.append(account_name[:-1])
            else:
                new_account_list.append(account_name)
        # 根据标题，内容，发布时间识别是否转载
        similar_article = self.find_ori_article_in_news(
            title, content, published_at)
        if similar_article:
            new_account_list.append(similar_article['medium_name'])
        # print(new_account_list)
        return list(set(new_account_list))

    def is_reprint(self, medium_id, medium_name, ori_medium_name,
                   mp_account_name, news_id, title, content, mp_type_id,
                   published_at):
        """
        文章转载识别
        :param medium_id(int): 媒体id
        :param medium_name(str): 媒体名
        :param mp_account_name(str): 媒体号名
        :param news_id(int): 文章id
        :param content(str): 文章内容
        :return:
        """
        # 提取文章首尾，hanlp抽取机构名
        # content = re.sub(r'<!--.*?-->|<script.*?/script>|<style.*?/style>|<.*?>', '', content)
        # content = content.strip()
        # new_content = content[-100:] + content[:50]
        # result = HanLP.segment(new_content)
        # self.logger.info(f'分词结果：{result}')
        account_name_list = []
        # # 针对财新官网渠道，直接返回原创
        # if mp_type_id == 11 and medium_name == '财新':
        #     self.logger.info(
        #         f'news:{title} is original from medium:{medium_name}')
        #     return [medium_name], [medium_id], []
        medium_list = [
            '界面新闻',
            '21世纪经济报道',
            '澎湃新闻',
            '南方周末',
            '人民日报',
            '南方日报',
            '每日经济新闻',
            '经济观察报',
        ]
        medium_dict = {
            '界面新闻': '界面',
            '21世纪经济报道': '21',
            '澎湃新闻': '澎湃',
            '南方周末': '南方周末',
            '人民日报': '人民日报',
            '南方日报': '南方日报',
            '每日经济新闻': '每日经济',
            '经济观察报': '经济观察报',
        }
        # 针对界面新闻官网渠道，判断是否原创
        if mp_type_id == 11 and ori_medium_name and medium_name in medium_list:
            # if not ori_medium_name:
            #     return [medium_name], [medium_id], []
            for medium in medium_list:
                if medium == medium_name and medium_dict[
                        medium] in ori_medium_name:
                    return [medium_name], [medium_id], []
            else:
                account_name_list.append(ori_medium_name)
        else:
            account_name_list = self.get_account_name2(title, content,
                                                       published_at,
                                                       account_name_list)

            # 若无机构名 或 内容包含匹配的媒体号名，则返回原媒体，否则继续
            if not account_name_list:
                self.logger.info(
                    f'news:{title} is original from medium:{medium_name}')
                return [medium_name], [medium_id], []
            for account_name in account_name_list:
                # 编辑距离判断该机构名是否与媒体号名相似，是则返回原媒体，否则继续
                if levenshtein(account_name, mp_account_name
                               ) < 2 or mp_account_name in account_name:
                    self.logger.info(
                        f'news:{title} is original from medium:{medium_name}')
                    return [medium_name], [medium_id], []
        account_names = []
        ori_medium_ids = []
        reprint_from = []
        # print(account_name_list)
        for account_name in account_name_list:
            # 查找新机构名是否在mp_account表，不在，则输出该机构名，在则继续
            ori_medium_id = self.find_similar_account(account_name)
            if not ori_medium_id:
                self.logger.info(
                    f'account_name:{account_name} is not find in mp_account')
                account_names.append(account_name)
                ori_medium_ids.append(None)
                reprint_from.append({
                    'title': '',
                    'url': '',
                    'media': account_name,
                })
            else:
                # 查找该机构下的本文章是否已被收录，否则返回新媒体id后结束，有则继续
                similar_article = self.find_similar_article_in_news(
                    account_name, ori_medium_id, title, content)
                if not similar_article:
                    account_names.append(account_name)
                    ori_medium_ids.append(ori_medium_id)
                    reprint_from.append({
                        'title': '',
                        'url': '',
                        'media': account_name,
                    })
                else:
                    # 寻找最初出处
                    for i in range(10):
                        try:
                            ori_new_id = int(similar_article['reprint_from']
                                             ['url'].split('/')[-1])
                            logger.info(f'find ori_news_id: {ori_new_id}')
                            similar_article = self.query_ori_article_in_news(
                                ori_new_id)
                        except:
                            ori_new_id = ori_medium_id
                        if not similar_article or 'reprint_from' not in similar_article.keys(
                        ):
                            account_names.append(account_name)
                            ori_medium_ids.append(ori_medium_id)
                            reprint_from.append({
                                'title': '',
                                'url': '',
                                'media': account_name,
                            })
                        elif len(similar_article['reprint_from']) == 0:
                            break
                    # 记录被转载的情况
                    reprint_to = {
                        'title': title,
                        'url':
                        'https://beta.mediarank.cn/news/' + str(news_id),
                        'media': medium_name,
                    }
                    self.update_reprint_to_in_news(similar_article, reprint_to)

                    account_names.append(account_name)
                    ori_medium_ids.append(ori_medium_id)
                    # 记录转载至的情况
                    reprint_from.append({
                        'title':
                        similar_article['title'],
                        'url':
                        'https://beta.mediarank.cn/news/' +
                        str(similar_article['id']),
                        'media':
                        similar_article['medium_name'],
                    })
        return account_names, ori_medium_ids, reprint_from

    def query_ori_article_in_news(self, news_id):
        """
        Query article info in table `news`.
        """
        must_query = [
            ('term', 'id', news_id),
        ]
        self.logger.info(f'query_article_in_news:{must_query}')
        sort_list = [('created_at', -1)]
        result_iter = self.table_cli.query(table_name='news',
                                           must_query_list=must_query,
                                           sort_list=sort_list,
                                           index_name='news_index')
        for query_result in result_iter:
            self.logger.info(f'获取到news原文章')
            return query_result
        return

    def write_reporters(
        self,
        data,
        new_medium_id,
        new_medium_name,
        reporter_name_list,
    ):
        """
        Write (or maybe update) reporters into database.

        :param data (dict): article data after categorize.
        :param new_medium_id (int): original medium id of article.
        :param news_id (int): id in table `news`.
        :param reporter_name_list (list): Reporter name list.
        :param reporter_type (int): 0 for reporter, 1 for correspondents.
        """
        medium_id = new_medium_id
        medium_name = new_medium_name
        news_id = data['news_id']
        reports_list = []
        # Write or update repoters info
        for reporter_name in reporter_name_list:
            reporter_info = self.query_reporter(reporter_name, medium_id)
            # If reporter has been found in table `reporter`.
            # Then add the reporter's article number of this article type.
            if reporter_info:
                pk = self.update_reporter(data, reporter_info)
                reporter_id = reporter_info['id']
                self.logger.info(f'Update reporter: {pk} {reporter_name}')
            # If reporter has not been found, write new article data.
            else:
                pk = self.put_reporter(data, news_id, reporter_name, medium_id,
                                       medium_name)
                reporter_id = pk['id']
                self.logger.info(f'Save reporter: {pk} {reporter_name}')
            # Save reporters id.
            reporter_dict = dict()
            reporter_dict['id'] = reporter_id
            reporter_dict['name'] = reporter_name
            reports_list.append(reporter_dict)
            self.logger.info(f'reports_list:{reports_list}')
        return reports_list

    def query_reporter(self, reporter_name, medium_id):
        """
        Query reporters info in table `reporter`.

        :param reporter_name [TODO:type]: [TODO:description]
        :param medium_id [TODO:type]: [TODO:description]
        """
        must_query = [
            ('term', 'medium_id', medium_id),
            ('term', 'type', 0),
            ('phrase', 'name', reporter_name),
        ]
        sort_list = [
            ('created_at', -1),
        ]
        self.logger.info(f'query_reporter:{must_query}')
        result_iter = self.table_cli.query('reporter',
                                           must_query_list=must_query,
                                           sort_list=sort_list,
                                           index_name='reporter_index')
        if not result_iter:
            return
        for reporter in result_iter:
            if reporter["name"] == reporter_name:
                self.logger.info(
                    f'Found reporter {reporter["name"]} in `reporter`.')
                return reporter

    def update_reporter(self, reporter_data, existed_reporter_info):
        """
        Update reporter info.

        :param data dict: Article data after processed.
        :param existed_reporter_info dict: reporter info exists in table.
        """
        data = deepcopy(reporter_data)
        news_type_list = existed_reporter_info.get('news_types', '')
        if not news_type_list:
            return
        news_type_list = json.loads(news_type_list)
        news_type_id = data['news_type_id']
        news_type_name = data['news_type_name']
        # Update news_type.
        for news_type_dict in news_type_list:
            if news_type_dict['id'] == news_type_id:
                news_type_dict['count'] += 1
                break
        else:
            t = {"id": news_type_id, "name": news_type_name, "count": 1}
            news_type_list.append(t)
        col = {
            'id':
            existed_reporter_info['id'],
            'random_num':
            existed_reporter_info['random_num'],
            'news_count':
            existed_reporter_info['news_count'] + 1,
            'word_count':
            existed_reporter_info.get('word_count', 0) + data['word_count'],
            'avg_word_count':
            (existed_reporter_info.get('word_count', 0) + data['word_count']) /
            (existed_reporter_info['news_count'] + 1),
            'updated_at':
            int(time.time()),
            'is_deleted':
            0,
            'news_types':
            json.dumps(sorted(news_type_list,
                              key=lambda news_type: news_type["count"],
                              reverse=True),
                       ensure_ascii=False),
        }
        reporter_data = data.get('reporter_data', {})
        if reporter_data:
            col = {**col, **reporter_data}
        pk = self.table_cli.update_row(table_name='reporter',
                                       pk_list=['random_num', 'id'],
                                       data=col)
        return pk

    def put_reporter(self, reporter_data, news_id, reporter_name, medium_id,
                     medium_name):
        """
        记者写入记者表
        [x] Test.

        :param data dict: Article data after processed.
        :param news_id int: news_id.
        :param reporter_name str: reporter name.
        """
        data = deepcopy(reporter_data)
        news_types = [{
            "id": data['news_type_id'],
            "name": data['news_type_name'],
            "count": 1
        }]
        try:
            gender, prob = ngender.guess(reporter_name)
            gender = 0 if gender == 'female' else 1
        except Exception:
            gender = 0
        province, city = self.query_medium_local(data['medium_id'])
        time_now = int(time.time())
        col = {
            'random_num': random.randint(0, 100),
            'id': None,
            'name': reporter_name,
            'extracted_name': reporter_name,
            'gender': gender,
            'avatar': '',
            'type': 0,
            'introduction': '',
            'score': 0,
            'medium_id': medium_id,
            'medium_name': medium_name,
            'province': province if data.get('province') else '',
            'city': city if city else '',
            'source_news_id': news_id,
            'source_news_title': data['title'],
            'news_count': 1,
            'word_count': data['word_count'],
            'avg_word_count': data['word_count'],
            'news_types': json.dumps(news_types, ensure_ascii=False),
            'created_at': time_now,
            'updated_at': time_now,
            'is_deleted': 0,
        }
        reporter_data = data.get('reporter_data', {})
        if reporter_data:
            col = {**col, **reporter_data}
        pk = self.table_cli.put_row('reporter',
                                    pk_list=['random_num', 'id'],
                                    data=col)
        return pk

    def write_correspondents(self,
                             data,
                             news_id,
                             correspondent_name_list,
                             correspondent_type=0):
        """
        Write (or maybe update) correspondents into database.

        :param data (dict): article data after categorize.
        :param news_id (int): id in table `news`.
        :param correspondent_name_list (list): correspondent name list.
        :param correspondent_type (int): 0 for correspondent, 1 for correspondents.
        """
        medium_id = data['medium_id']
        correspondents_list = []
        # Write or update repoters info
        for correspondent_name in correspondent_name_list:
            correspondent_info = self.query_correspondent(
                correspondent_name, medium_id)
            # If correspondent has been found in table `correspondent`.
            # Then add the correspondent's article number of this article type.
            if correspondent_info:
                pk = self.update_correspondent(data, correspondent_info)
                correspondent_id = correspondent_info['id']
                self.logger.info(
                    f'Update correspondent: {pk} {correspondent_name}')
            # If correspondent has not been found, write new article data.
            else:
                pk = self.put_correspondent(data, news_id, correspondent_name)
                correspondent_id = pk['id']
                self.logger.info(
                    f'Save correspondent: {pk} {correspondent_name}')
            # Save correspondents id.
            correspondents_list.append({
                'id': correspondent_id,
                'name': correspondent_name
            })
        return correspondents_list

    def query_correspondent(self, correspondent_name, medium_id):
        """
        Query correspondents info in table `correspondent`.

        :param correspondent_name [TODO:type]: [TODO:description]
        :param medium_id [TODO:type]: [TODO:description]
        """
        must_query = [
            ('term', 'medium_id', medium_id),
            ('phrase', 'name', correspondent_name),
        ]
        sort_list = [
            ('id', -1),
        ]
        self.logger.info(f'query_correspondent:{must_query}')
        result_iter = self.table_cli.query('reporter',
                                           must_query_list=must_query,
                                           sort_list=sort_list,
                                           index_name='reporter_index')
        for correspondent in result_iter:
            self.logger.info(
                f'Found correspondent {correspondent["name"]} in `correspondent`.'
            )
            return correspondent

    def update_correspondent(self, correspondent_data,
                             existed_correspondent_info):
        """
        Update correspondent info.

        :param data dict: Article data after processed.
        :param existed_correspondent_info dict: correspondent info exists in table.
        """
        data = deepcopy(correspondent_data)
        news_type_list = existed_correspondent_info.get('news_type', '')
        if not news_type_list:
            return
        news_type_list = json.loads(news_type_list)
        news_type_id = data['news_type_id']
        news_type_name = data['news_type_name']
        # Update news_type.
        for news_type_dict in news_type_list:
            if news_type_dict['id'] == news_type_id:
                news_type_dict['count'] += 1
                break
        else:
            t = {"id": news_type_id, "name": news_type_name, "count": 1}
            news_type_list.append(t)
        col = {
            'id':
            existed_correspondent_info['id'],
            'random_num':
            existed_correspondent_info['random_num'],
            'news_count':
            existed_correspondent_info['news_count'] + 1,
            'word_count':
            existed_correspondent_info.get('word_count', 0) +
            data['word_count'],
            'avg_word_count':
            (existed_correspondent_info.get('word_count', 0) +
             data['word_count']) /
            (existed_correspondent_info['news_count'] + 1),
            'updated_at':
            int(time.time()),
            'news_type':
            json.dumps(news_type_list, ensure_ascii=False),
        }
        pk = self.table_cli.update_row(table_name='reporter',
                                       pk_list=['random_num', 'id'],
                                       data=col)
        return pk

    def put_correspondent(self, correspondent_data, news_id,
                          correspondent_name):
        """
        通讯员写入记者表
        [x] Test.

        :param data dict: Article data after processed.
        :param news_id int: news_id.
        :param correspondent_name str: correspondent name.
        """
        data = deepcopy(correspondent_data)
        news_type = [{
            "id": data['news_type_id'],
            "name": data['news_type_name'],
            "count": 1
        }]
        try:
            gender, prob = ngender.guess(correspondent_name)
            gender = 0 if gender == 'female' else 1
        except Exception:
            gender = 0
        province, city = self.query_medium_local(data['medium_id'])
        time_now = int(time.time())
        col = {
            'random_num': random.randint(0, 100),
            'id': None,
            'name': correspondent_name,
            'extracted_name': correspondent_name,
            'gender': gender,
            'avatar': '',
            'type': 1,
            'introduction': '',
            'score': 0,
            'medium_id': data['medium_id'],
            'medium_name': data['medium_name'],
            'province': province if data.get('province') else '',
            'city': city if city else '',
            'source_news_id': news_id,
            'source_news_title': data['title'],
            'news_count': 1,
            'word_count': data['word_count'],
            'avg_word_count': data['word_count'],
            'news_types': json.dumps(news_type, ensure_ascii=False),
            'created_at': time_now,
            'updated_at': time_now,
        }
        pk = self.table_cli.put_row('reporter',
                                    pk_list=['random_num', 'id'],
                                    data=col)
        return pk

    def row_format(self, row):
        row_dict = {}
        if type(row) is ots.Row:
            for col_name, col_data in row.primary_key:
                row_dict[col_name] = col_data
            for col_name, col_data, _ in row.attribute_columns:
                row_dict[col_name] = col_data
        else:
            for col_name, col_data in row[0]:
                row_dict[col_name] = col_data
            for col_name, col_data, _ in row[1]:
                row_dict[col_name] = col_data
        return row_dict

    def rows_format(self, rows):
        row_dict_list = []
        for row in rows:
            row_dict_list.append(self.row_format(row))
        return row_dict_list

    def get_comments(self, article_id):
        all_comments = []
        next_token = None
        while True:
            rows, next_token, total_count, is_all_succeed = self.table_ots.search(
                'mp_news_comment',
                'mp_news_comment_index',
                ots.SearchQuery(
                    ots.BoolQuery(
                        must_queries=[
                            ots.TermQuery('mp_article_id', article_id),
                        ],
                        must_not_queries=[ots.ExistsQuery('news_id')]),
                    # get_total_count=True,
                    # offset=0,
                    sort=ots.Sort([ots.PrimaryKeySort()])
                    if not next_token else None,
                    next_token=next_token,
                    limit=100),
                ots.ColumnsToGet([], ots.ColumnReturnType.ALL))
            comments = self.rows_format(rows)
            all_comments += comments
            if not next_token:
                return all_comments

    def update_comments(self, comment_data):
        comment = deepcopy(comment_data)
        pk = self.table_cli.update_row(table_name='mp_news_comment',
                                       pk_list=['medium_id', 'id'],
                                       data=comment)
        self.logger.info(f'update comments success!')
        return pk

    def update_comment_with_news_id(self, news_id, all_news_id, article_id):
        comment_datas = self.get_comments(article_id)
        if not comment_datas:
            return
        for comment_data in comment_datas:
            comment = deepcopy(comment_data)
            comment['news_id'] = news_id
            comment['all_news_id'] = all_news_id
            comment['updated_at'] = int(time.time())
            self.update_comments(comment)

    # def get_strip_content(self, content):
    #     """
    #     Get clean text:
    #     remove spaces, chinese spaces, endlines, &nbsp, HTML tags.

    #     :param content (str): Html content.
    #     """
    #     return clear_all_html(content)


if __name__ == "__main__":
    ah = ArticleHandler()
    # name_list = []
    # content = '<article><p>这一数字来自本周五提交给全国人民代表大会的预算报告草案。</p><p>分析人士表示，这意味着尽管新冠肺炎疫情带来了经济影响，但中国可以为军事发展提供足够的资金，而尽管增速有所放缓，这符合中国在新冠肺炎疫情后的当前经济形势。</p><p>2019年中国国防预算为1.19万亿元，比2018年增长7.5%。自2016年以来，中国的年度国防预算保持了个位数的增长。</p><div class="pgc-img"><img src="http://p1.pstatp.com/large/pgc-image/ea57fa5145f8431896401b87d3825228.png" width="640" height="364" thumb_width="120" thumb_height="68" ></img><p class="pgc-img-caption"></p></div><p>来源：环球时报英文版</p></article>'
    # content = '<article><p>据新华社电,这一数字来自本周五提交给全国人民代表大会的预算报告草案。</p><p>分析人士表示，这意味着尽管新冠肺炎疫情带来了经济影响，但中国可以为军事发展提供足够的资金，而尽管增速有所放缓，这符合中国在新冠肺炎疫情后的当前经济形势。</p><p>2019年中国国防预算为1.19万亿元，比2018年增长7.5%。自2016年以来，中国的年度国防预算保持了个位数的增长。</p><div class="pgc-img"><img src="http://p1.pstatp.com/large/pgc-image/ea57fa5145f8431896401b87d3825228.png" width="640" height="364" thumb_width="120" thumb_height="68" ></img><p class="pgc-img-caption"></p></div></article>'
    # content = '<article><p>这一数字来自本周五提交给全国人民代表大会的预算报告草案。</p><p>分析人士表示，这意味着尽管新冠肺炎疫情带来了经济影响，但中国可以为军事发展提供足够的资金，而尽管增速有所放缓，这符合中国在新冠肺炎疫情后的当前经济形势。</p><p>2019年中国国防预算为1.19万亿元，比2018年增长7.5%。自2016年以来，中国的年度国防预算保持了个位数的增长。来源：环球时报英文版\新华社  记者 张晓明'
    # new_account_list = ah.get_account_name2(content, name_list)
    # print(new_account_list)
    # medium_id = 11111
    # medium_name = '南方周末'
    # mp_account_name = '南方周末'
    # ori_medium_name = '21世纪'
    # news_id = 11111111111
    # title = '呵呵哈哈哈或或'
    # content = '奋斗的实施改革撒范德萨发打发第三方'
    # mp_type_id = 11
    # account_names, ori_medium_ids, reprint_from = ah.is_reprint(
    #     medium_id, medium_name, ori_medium_name, mp_account_name, news_id,
    #     title, content, mp_type_id)
    # print(account_names, ori_medium_ids, reprint_from)
    account_name = '等深线'
    medium_id = 1589611478810000
    title = '等深线：上海富商密春雷“秘史”'
    content = """
    <article><p><strong>中国经营报《等深线》</strong>记者 万佳丽 上海报道</p><p><br></p><p>密春雷，一个上海富豪。</p><p><br></p><p>2020年4月21日，位于上海市静安区江宁社区C050201单元023-7商办地块以60亿元成交，成为上海市今年来土地总价第二高的成交地块，而背后的受让方正是览海控股集团有限公司（以下简称“<strong>览海控股</strong>”），其实际控制人系央视主持人董卿的老公——上海滩富豪<strong>密春雷</strong>。</p><p><br></p><p><strong>《等深线》</strong>（ID：<strong>depthpaper</strong>）记者在调查过程中发现，览海控股、上海人寿以及览海医疗（600896，SH）的实控人密春雷近年来发展快速，之后其一系列投资以及投资的资金来源也颇为神秘，记者在调查中试图揭开这层神秘的面纱。</p><p><br></p><p><strong>密春雷老家</strong></p><p><br></p><p>1200平方公里的崇明岛，风景秀丽。外地人乃至一些上海人都以为崇明岛全部是上海市崇明区。实际上，在崇明岛的北部，有一小部分是归属江苏省。永隆沙、兴隆沙和新村沙这三块地方，归属江苏省海门市和启东市。两市分别在崇明岛上设海永镇和启隆镇，来管理归属于各自的区域。</p><p><br></p><p>1978年12月，密春雷出生在属于上海市崇明区的一个村上的农民家庭，是家中独子。1973年出生的董卿，其老家亦在崇明岛，属于江苏启东的启隆镇。2020年4月23日下午，《等深线》记者前往崇明岛探访，密春雷老家的多位邻居描述，密春雷小名叫“小牛”，性情温和，从小脾气好，没看他跟别人吵过架。</p><p><br></p><div class="pgc-img"><img src="http://p1.pstatp.com/large/pgc-image/60c30eee97cc4d52954846a531daed8d.png" width="640" height="627" thumb_width="120" thumb_height="118" ></img><p class="pgc-img-caption">密春雷在家门口修的一条小路 《等深线》记者 万佳丽 摄</p></div><p><br></p><p>密春雷老家是在崇明岛中部的庙镇镇庙中村。密春雷在早期公司的材料申报中，将老家地址填报为庙镇镇农民街。而今的庙镇镇农民街，沿街分布着法庭、小学等，如果没有疫情，这里的街道平时会比较热闹。密春雷家最早的一处住宅也在庙中村，卖掉了此处的住宅后，密春雷家在距离老住宅100米左右的地方新建了一个占地颇大，带有近百平方小院子的别墅。</p><p><br></p><p>进出这套别墅的小路，当地人介绍是密春雷出资修建的，密春雷的家就在小路尽头右手边。邻居家的老人说，密春雷一家很少回这老房子，可能一年不一定能回来一次，记得前两年清明回来过，今年和去年都没有看到他们回来。</p><p><br></p><p>当地人告诉记者，密春雷没上大学，很年轻的时候就开始做生意了。</p><p><br></p><p>据记者多方了解，密春雷最初是在崇明公安局交通队跑运输，后来和老婆金晶（做生意前是实验小学一名老师）收了家公司开始做起工程。</p><p><br></p><div class="pgc-img"><img src="http://p1.pstatp.com/large/pgc-image/bf477b758269465e957371029c62e5a0.png" width="640" height="479" thumb_width="120" thumb_height="90" ></img><p class="pgc-img-caption">密春雷目前的崇明老家 《等深线》记者 万佳丽 摄</p></div><p><br></p><p>记者查阅工商信息系统，1992年10月8日注册的上海崇明公路物资有限公司，目前股东中，密春雷持股80%，金晶持股20%。企业信用信息公示系统中显示， 上海崇明公路物资有限公司 法定代表人为吴琦。其经营范围包括建材、沥青、金属材料等。密春雷目前担任执行董事，金晶担任监事，吴琦任总经理。2017年1月27日，法定代表人由密春雷变更为吴琦。上海崇明公路物资有限公司对外投资了上海崇明公路工程养护有限公司，旗下还有7家分支机构。</p><p><br></p><p>《等深线》记者在进一步的查询中还了解到，1994年7月1日成立的上海崇明公路建设有限公司，目前法定代表人为密伯元（《等深线》记者多方核实，系密春雷父亲），监事为金晶。公司经营范围为公路桥梁工程建筑、给排水工程建筑、公路养护维修、公路设备租赁、土石方工程。《崇明县志》（1985—2004）中收集了以20世纪80年代前早市停止为标志而湮没的集镇56个。《崇明县志》还记录了上世纪90年代崇明岛经济迅速发展，交通等基础设施快速建设。无疑，密春雷家族正是赶上了90年代的发展机遇。90年代的时候，年轻的密春雷，喜欢在欣欣向荣的街道上跑步。</p><p><br></p><p>许久也难回老家一趟的密春雷，村民们难以看到其身影。村里年迈的老人，喜欢去正在整治的河道边，看看新村的变化。而在密春雷家附近墙上的村民公示栏，一则2019年12月30日的”10队农户领各单位粮补清单”上，密伯元和其母亲共领了704元。</p><p><br></p><p>此外，记者在探访期间还独家获悉，密春雷的母亲叫钱冠军。钱冠军持有上海中瀛产业股份有限公司20%股权，上海览海物业管理有限公司30%股权，同时在数十个密春雷相关公司担任监事。从密春雷早期关联的公司看，这些公司都是其夫妇或者父母构成的家族企业。密春雷家族早期的公司中，还有设立在崇明岛南门的记录。由于时间过去了二三十年，已经无法探寻。唯有密春雷前妻金晶早期登记的地址还在南门新南路一处居民区。《等深线》记者现场探访发现，该处住房位于该住宅区某栋6层，从燃气账单等可以看到居住人员已经变更。该处小区保安已经记不得有这样一位金女士。</p><p><br></p><p><strong>不断进化</strong></p><p><br></p><p>《等深线》记者发现，本是扎根崇明岛建筑交通领域的密氏家族公司，在2003年开始渐渐进化。</p><p><br></p><p>2003年9月，密春雷和其父亲密伯元分别出资4000万元和1000万元，在老家崇明县（如今是崇明区）津桥经济开发区成立了上海中瀛企业发展有限公司，公司注册资金共5000万元。这家公司正是览海集团的前身。注册资金5000万元，按照当时的相关管理办法，注册资金需要实缴。这意味着，2003年9月前后，密春雷和其父亲资金实力已经较为雄厚。</p><p><br></p><p>“听他自己后来和老家的人说是做期货赚了一笔。”知情人士说道。期货的故事，在许多上海大佬的传说中，似乎都是相生相伴。然而，即使是其亲口所言，或许也未必是真。</p><p><br></p><p>随后，览海控股集团前身上海中瀛成立，密春雷的事业进入了快速发展期。目前，其控制的览海控股旗下投资了保险、银行、地产、医疗、汽车、煤矿等各类资产，逐渐发展成现在的“资本帝国”。</p><p><br></p><p>览海控股成立之后，频繁增资是其特征之一。根据记者掌握的工商信息显示，览海控股一共经历了7次增资，公司注册资本由最初的5000万元增加到65亿元。</p><p><br></p><p>第一次：2004年2月，公司变更注册资本为8000万元，由原股东密春雷增加资本金3000万元，密伯元出资额不变，变更后股东出资比例为密春雷87.5%，密伯元12.5%。同年8月，将原注册登记在工商崇明分局迁至上海市工商局注册登记。同时在2004年7月28日，因组建集团，将上海中瀛企业发展有限公司变更为上海中瀛企业（集团）有限公司。</p><p><br></p><p>第二次：2013年11月19日，密春雷增加资本金8000万元，公司注册资金扩充到1.6亿元，而密伯元出资额不变，变更后股东出资比例为密春雷93.75%，密伯元6.25%。</p><p><br></p><p>第三次：2013年11月28日，密春雷增加资本金5000万元，公司注册资金扩充到2.1亿元，而密伯元出资额不变，变更后股东出资比例为密春雷95.24%，密伯元4.76%。</p><p><br></p><p>2014年8月29日，上海中瀛企业发展有限公司变更为览海控股（集团）有限公司。2014年10月底，览海控股将公司住所搬至上海自贸区加枫路26号6层。记者在走访时得知，览海控股目前办公场所已不在此处。该处物业和保安均不记得有这样一个公司存在。</p><p><br></p><p>第四次：2016年2月，公司变更注册资本为10亿元，其中密春雷认缴9.9亿元，持股99%，密伯元认缴1000万元，持股1%。2016年4月，再次变更注册资本为20亿元，密春雷货币认缴出资额增资到19.8亿元，密伯元认缴出资额增资到2000万元。</p><p><br></p><p>第五次：2016年9月，继续将公司注册资本增加至30亿元，其中密春雷出资29.7亿元，持股99%，密伯元出资3000万元，持股1%。</p><p><br></p><p>第六次：2016年10月，继续将公司注册资本增加至60亿元，其中密春雷出资59.4亿元，持股99%，密伯元出资6000万元，持股1%。</p><p><br></p><p>第七次：2018年12月，新股东上海丰道正达投资有限公司认购5亿元，持股7.69%。而上海丰道正达投资有限公司股东叫钱冠军。记者独家获悉，钱冠军正为密春雷母亲。</p><p><br></p><p>从这些变化可以看出，自2015年开始，览海控股的注册资本开始快速且大幅增加，这或许与其开始加快资本布局有关。</p><p><br></p><p><strong>系列布局</strong></p><p><br></p><p>2015年2月，览海控股联合中海集团投资有限公司、上海电气（集团）、上海城投资产经营有限公司等共同发起设立了上海人寿保险股份有限公司（以下简称“上海人寿”），览海控股持股比例20%，为上海人寿单一最大股东，公司初始注册资本20亿元。进军保险，成为了2015年前后众多资本的战略布局。</p><p><br></p><p>2015年，对于各路资本系而言是一个重要节点。2012年薄王事件和随之而来的反腐力度加大，一些资本系经历了两三年的消停后，又开始蠢蠢欲动。览海是否在这时候搭建上了更加具有实力的资本系呢？《等深线》记者将在后续追踪报道。</p><p><br></p><p>2016年，经原保监会批准，上海人寿变更注册资本至60亿元。通过此次增资扩股，上海人寿引入3家新股东——洋宁实业、和翠实业及上海幸连贸易有限公司，增资后3家股东持股比例分别为13.75%、13.75%、3%。</p><p><br></p><div class="pgc-img"><img src="http://p1.pstatp.com/large/pgc-image/67c34769bc4a44cf81a14744488e4cc5.png" width="640" height="642" thumb_width="120" thumb_height="120" ></img><p class="pgc-img-caption"></p></div><p>但之后，上海人寿被曝出洋宁实业、和萃实业在2016年的增资申请中隐瞒与控股股东览海控股的关联关系以及超比例持股，提供虚假材料，在2018年4月被银保监会要求清退违规股权。</p><p><br></p><p>直到今年4月8日，上海人寿发布变更股东公告称，上海和萃实业有限公司、上海洋宁实业有限公司各将所持有的上海人寿13.75%股权，转让给览海控股（集团）有限公司、上海中静安银投资有限公司、上海银润控股（集团）有限公司、大连迈隆国际物流有限公司4家公司，转让完成后二者将完全退出上海人寿股东名单。此次股权转让后，第一大股东览海集团持股比例将由20%提升至32.8%。</p><p><br></p><p>搭建上海人寿的2015年，览海控股开始尝试控壳一家上市公司。</p><p><br></p><p>2015年6月，彼时的中海海盛（600896.SH）公告，拟以6.85元/股的价格，向上海览海投资有限公司（以下简称“览海投资”）发行2.9亿股，募资不超过20亿元。密春雷旗下的览海上寿也受让了8200万股中海海盛股票，本次定向增发完成后，将占总股本9.39%；览海投资将持有股份比例为33.43%，两者合计持有42.82%股份。本次发行完成后，第一大股东将变更为览海投资，实际控制人将变更为密春雷。</p><p><br></p><p>览海上寿仅是一家平台公司，在收购中海海盛前夕，于2015年5月成立，其中览海控股持股51%，上海人寿持股49%。为何又要临时成立一家公司去收购上市公司中海海盛的股权呢？</p><p><br></p><p>成功拿下中海海盛的控制权后，密春雷清空了中海海盛原本的航运资产，装入医疗资产，中海海盛向医疗健康领域转型，最终改名为“览海医疗”。</p><p><br></p><p>之后进一步提高持股比例巩固控制权，在2017年12 月19日至2018年12月31日期间，上海览海通过上交所集中竞价交易系统累计增持了上市公司览海医疗股份12672111股。览海投资合计持有览海医疗股份304642913股，占览海医疗总股本的35.05%。上海览海及其一致行动人览海上寿、上海人寿合计持有览海医疗股份407621632股，占公司总股本的46.90%。</p><p><br></p><p>值得注意的是，截至目前，览海投资控股股东及其一致行动人已累计质押的股票数量为170243000股，占其持股总数的41.76%，占公司总股本的19.59%。</p><p><br></p><p>览海投资是密春雷“览海系”的核心股权投资平台，是览海医疗产业投资股份公司（上市公司览海医疗）的第一大股东，最新持股比例为35.05%。而览海上寿则是览海集团与上海人寿共同成立的医疗产业投资平台，持有览海医疗9.44%股权。</p><p><br></p><p>拿下上海人寿这块保险牌照，只是密春雷在金融领域布局的开始。之后，他又接连受让了上海农商行、曲靖市商业银行的部分股权。</p><p><br></p><p>2016年12月，览海控股斥资18.9亿元“接手”绿地控股所持上海农商行4%股权（即2亿股股份）。截至2019年末，览海控股持有3.36亿股，占上海农商行总股本 3.87%，位列第十大股东。</p><p><br></p><p>后经览海控股提名，张锡麟担任上海农商行监事，黄坚担任非执行董事，黄坚还在览海医疗产业投资股份有限公司担任董事。</p><p><br></p><p>2019年截至报告期末，览海控股与其关联方、一致行动人合并持有本公司3.87%股份，出质上海农商行3.2亿股股份，质押股份数占其持股总数的95.24%。</p><p><br></p><p>也许是对上海农商行没有实现控制权，览海控股又继续收购了曲靖市商业银行股份有限公司（以下简称“曲靖商业银行”）。</p><p><br></p><p>2018年4月，览海集团认购曲靖商业银行4.92亿股股份，持股比例19.50%，与云南省水务产业投资有限公司并列第一大股东，与览海控股同一时间进入的新股东还有紫光集团。</p><p><br></p><p>2019年8月，云南银保监局核准王建平曲靖市商业银行董事长任职资格。据悉，王建平由该行股东览海控股提名出任董事长。另一名董事石福梁也由第一大股东览海控股提名，其此前任上海人寿保险股份有限公司总裁、览海控股党委书记。</p><p><br></p><p>在控股保险银行之后，密春雷也并没有停下其资本布局的脚步，其继续大手笔四处收购汽车、地产、医疗等资产。</p><p><br></p><p>2019年4月，润东汽车（1365.HK）发布公告，与昆明彦恒汽车销售服务有限公司（以下简称“昆明彦恒”）签订转让股份的意向协议，拟向昆明彦恒出售4家间接全资附属公司（即：润东汽车集团有限公司、徐州润东汽车营销管理有限公司、徐州悦美汽车营销管理有限公司及徐州润东交广汽车营销管理有限公司）的全部股权，出售价格约为人民币34亿元。昆明彦恒公司背后的实控人正是密春雷。</p><p><br></p><p>公告中的这4家附属公司直接或间接持有及管理润东汽车集团的62家附属公司，主要包括山东、安徽、江苏、浙江及上海经营合共56家汽车经销店。</p><p><br></p><p>除了保险、银行、融资租赁、医疗健康、汽车以及地产等资产，密春雷还在内蒙古拥有煤矿资产。密春雷投资35亿元与内蒙古平庄煤业集团合资成立内蒙古中瀛天山能源开发有限公司，对内蒙古赤峰市绍根煤田阿根塔拉矿区的煤炭资源进行开发。</p><p><br></p><p>除了在内地布局的系列公司之外，密春雷早在2004年就开始布局香港。《等深线》记者从香港公司注册处查询到，密春雷在香港至少有2家公司，其中中瀛控股（香港）有限公司（ZHONGYING HOLDINGS （HONG KONG） CO.,LIMITED），成立于2004年10月13日，于2010年3月解散，股东为密春雷；中国览海医疗集团（香港）有限公司（China Lanhai Medical Group （HK） Limited），成立于2014年12月，股东为密春雷。此外，览海国际贸易有限公司（LanHai International Trading Limited）注册在开曼群岛，成立于2015年9月，股东为China Lanhai Medical Group CO., LIMITED。这些香港公司和离岸公司，将会在密春雷的布局中扮演怎样的角色呢？《等深线》记者将会持续追踪。</p><p><br></p><p>4月的崇明岛，鸟语花香，密春雷儿时游泳过的小河河水已被抽干，正在进行大规模修理整治。最后的春光里，密春雷斥资60亿元零溢价拍下静安区黄金地块。“小牛”还在加速快跑！</p><p>（编辑：郝成 校对：颜京宁）</p><p><br></p><p>【<strong>等深线</strong>】（ID:<strong>depthpaper</strong>）是依托《中国经营报》推出的原创深度报道新媒体产品，关注泛财经领域的重大新闻事件及其新闻事件背后的逻辑与真 相。我们力图通过详实的调查、周密的采访和深入的讨论，勾勒新闻事件和焦点议题的全貌，与您一起“<strong>深度下潜，理解真相</strong>”。</p><p><br></p><p>欢迎提供新闻线索</p><p>E-mail：haocheng@cbnet.com.cn</p><p>电话：010-88890008</p><p>​</p></article>
    """
    query_result = ah.find_similar_article_in_news(account_name, medium_id,
                                                   title, content)
    ah.logger.info(f'query_result: {query_result["title"]}')
