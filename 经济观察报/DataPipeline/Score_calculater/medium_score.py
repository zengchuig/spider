#coding: utf-8
import json
import time
import datetime
import math
from copy import deepcopy

import aliyun_db as aliyun_db
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MedScoreHandler(object):
    def __init__(self):
        # self.table_cli = aliyun_db.get_unofficial_product_cli()
        self.table_cli = aliyun_db.get_unofficial_test_cli()
        self.logger = logger

    def query_score_in_ts(self, medium_id, scoretype, timestamp1):
        """
        查询媒体是否有榜单

        :param medium_id [int]: 媒体id.
        :param timestamp1 [int]: 榜单时间戳.
        :return
        """
        must_query = [
            ('term', 'medium_id', medium_id),
            ('term', 'rank_date', timestamp1),
            ('term', 'cycle', scoretype),
        ]
        self.logger.info(f'query medium_socre_in ts_medium_score:{must_query}')
        sort_list = [('rank_date', -1)]
        result_iter = self.table_cli.query(table_name='ts_medium_score',
                                           must_query_list=must_query,
                                           sort_list=sort_list,
                                           index_name='ts_medium_score_index')
        for query_result in result_iter:
            self.logger.info(f'查到该媒体的榜单')
            return query_result
        return

    def query_medium(self, medium_id):
        """
        查询媒体
        """
        must_query = [
            ('term', 'id', medium_id),
        ]
        sort_list = [('created_at', -1)]
        result_iter = self.table_cli.query(table_name='medium',
                                           must_query_list=must_query,
                                           sort_list=sort_list,
                                           index_name='medium_index')
        for query_result in result_iter:
            self.logger.info(f'查询到该媒体')
            return query_result
        return

    def put_score(self, news_data, medium_id, scoretype, daycount, timestamp1):
        """
        插入榜单
        """
        data = deepcopy(news_data)
        score_data = {}
        medium = self.query_medium(medium_id)
        if medium:
            score_data['province'] = medium['province']
            score_data['city'] = medium['city']
            news_type_id = data['news_type_id']
            news_type_name = data['news_type_name']
            score_data['news_types'] = json.dumps([{
                "id": news_type_id,
                "name": news_type_name,
                "count": 1,
            }],
                                                  ensure_ascii=False)
            score_data['news_count'] = 1
            score_data['word_count'] = data['word_count']
            score_data['read_count'] = data['read_count']
            score_data['avg_read_count'] = data['read_count']
            score_data['like_count'] = data['like_count']
            score_data['comment_count'] = data['comment_count']
            score_data['share_count'] = data['share_count']
            score_data['interact_count'] = data['interact_count']
            score_data['cycle'] = scoretype
            score_data['rank_date'] = timestamp1
            now_time = int(time.time())
            score_data['created_at'] = now_time
            score_data['updated_at'] = now_time
            sta_W = 1000 * float(
                math.log(score_data['word_count'] + 1, math.e) /
                math.log(20000 * daycount + 1.1, math.e))
            sta_R = 1000 * float(
                math.log(score_data['read_count'] + 1, math.e) /
                math.log(7000000 * daycount + 1.1, math.e))
            sta_Ra = 1000 * float(
                math.log(score_data['avg_read_count'] + 1, math.e) /
                math.log(100000 + 1.1, math.e))
            sta_L = 1000 * float(
                math.log(score_data['like_count'] + 1, math.e) /
                math.log(200000 * daycount + 1.1, math.e))
            sta_C = 1000 * float(
                math.log(score_data['comment_count'] + 1, math.e) /
                math.log(60000 * daycount + 1.1, math.e))
            score_data['score'] = int(sta_W * 0.1 + sta_R * 0.45 +
                                      sta_Ra * 0.2 + sta_L * 0.1 +
                                      sta_C * 0.15)
            score_data['id'] = None
            score_data['medium_id'] = medium_id
            print(score_data)
            pk = self.table_cli.put_row(table_name='ts_medium_score',
                                        pk_list=['medium_id', 'id'],
                                        data=score_data)
            print(f'Write ts_medium_score succeed:{pk}.')

            return score_data

    def update_score(self, result_row, data, daycount):
        """
        更新榜单
        """
        score_data = deepcopy(result_row)
        news_type_id = data['news_type_id']
        news_type_name = data['news_type_name']
        news_types = json.loads(result_row.get('news_types', json.dumps([])))
        if news_types:
            for news_type_dict in news_types:
                if news_type_dict['id'] == news_type_id:
                    news_type_dict['count'] += 1
                    break
            else:
                t = {"id": news_type_id, "name": news_type_name, "count": 1}
                news_types.append(t)
            score_data['news_types'] = json.dumps(
                sorted(news_types,
                       key=lambda news_type: news_type["count"],
                       reverse=True),
                ensure_ascii=False,
            )
        else:
            news_types = {
                "id": news_type_id,
                "name": news_type_name,
                "count": 1
            }
            score_data['news_types'] = json.dumps(
                [news_types],
                ensure_ascii=False,
            )
        score_data['news_count'] = score_data['news_count'] + 1
        score_data[
            'word_count'] = score_data['word_count'] + data['word_count']
        score_data[
            'read_count'] = score_data['read_count'] + data['read_count']
        score_data['avg_read_count'] = int(score_data['read_count'] /
                                           score_data['news_count'])
        score_data[
            'like_count'] = score_data['like_count'] + data['like_count']
        score_data['comment_count'] = score_data['comment_count'] + data[
            'comment_count']
        score_data[
            'share_count'] = score_data['share_count'] + data['share_count']
        score_data['interact_count'] = score_data['interact_count'] + data[
            'interact_count']
        now_time = int(time.time())
        score_data['updated_at'] = now_time
        sta_W = 1000 * float(
            math.log(score_data['word_count'] + 1, math.e) /
            math.log(20000 * daycount + 1.1, math.e))
        sta_R = 1000 * float(
            math.log(score_data['read_count'] + 1, math.e) /
            math.log(7000000 * daycount + 1.1, math.e))
        sta_Ra = 1000 * float(
            math.log(score_data['avg_read_count'] + 1, math.e) /
            math.log(100000 + 1.1, math.e))
        sta_L = 1000 * float(
            math.log(score_data['like_count'] + 1, math.e) /
            math.log(200000 * daycount + 1.1, math.e))
        sta_C = 1000 * float(
            math.log(score_data['comment_count'] + 1, math.e) /
            math.log(60000 * daycount + 1.1, math.e))
        score_data['score'] = int(sta_W * 0.1 + sta_R * 0.45 + sta_Ra * 0.2 +
                                  sta_L * 0.1 + sta_C * 0.15)
        print(score_data)
        pk = self.table_cli.update_row(table_name='ts_medium_score',
                                       pk_list=['medium_id', 'id'],
                                       data=score_data)
        print(f'Update ts_medium_score succeed:{pk}.')
        return score_data

    def handler(self, all_news_data):
        """
        主函数

        :return:
        """
        self.logger.info(f'媒体{all_news_data["medium_id"]}')
        medium_id = all_news_data['medium_id']
        self.logger.info('开始媒体榜单计算')
        # 日榜处理
        scoretype = 1
        daycount = 1
        today = datetime.date.today()
        # 当天开始时间戳
        timestamp1 = int(time.mktime(time.strptime(str(today), '%Y-%m-%d')))
        if int(time.time() < timestamp1 + 43200):
            # 昨天结束时间戳
            timestamp2 = int(time.mktime(time.strptime(str(today),
                                                       '%Y-%m-%d'))) - 1
            # 昨天开始时间戳
            timestamp1 = timestamp2 - 86399
        # 查询该媒体是否已有日榜
        result_row = self.query_score_in_ts(medium_id, scoretype, timestamp1)
        if result_row:
            self.update_score(result_row, all_news_data, daycount)
        else:
            self.put_score(all_news_data, medium_id, scoretype, daycount,
                           timestamp1)

        # 周榜处理
        scoretype = 2
        daycount = 7
        # 一周前开始时间戳
        today = datetime.date.today()
        today = today - datetime.timedelta(days=today.weekday())
        timestamp1 = int(time.mktime(time.strptime(str(today), '%Y-%m-%d')))
        # 查询该媒体是否已有周榜
        result_row = self.query_score_in_ts(medium_id, scoretype, timestamp1)
        if result_row:
            score_data = self.update_score(result_row, all_news_data, daycount)
        else:
            score_data = self.put_score(all_news_data, medium_id, scoretype,
                                        daycount, timestamp1)
        # 更新媒体表score
        if score_data:
            medium_data = self.query_medium(score_data['medium_id'])
            medium_data['score'] = score_data['score']
            pk = self.table_cli.update_row(table_name='medium',
                                           pk_list=['random_num', 'id'],
                                           data=medium_data)
            print(f'Update medium score succeed:{pk}.')

        # 月榜处理
        scoretype = 3
        daycount = 30
        # 一个月前开始时间戳
        today = datetime.date.today().replace(day=1)
        timestamp1 = int(time.mktime(time.strptime(str(today), '%Y-%m-%d')))
        # 查询该媒体是否已有月榜
        result_row = self.query_score_in_ts(medium_id, scoretype, timestamp1)
        if result_row:
            self.update_score(result_row, all_news_data, daycount)
        else:
            self.put_score(all_news_data, medium_id, scoretype, daycount,
                           timestamp1)


if __name__ == '__main__':
    ah = MedScoreHandler()
    # ah.handler()
