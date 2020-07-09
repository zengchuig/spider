#coding: utf-8
import json
import time
import datetime
import math
from copy import deepcopy

import tablestore as ots
from tablestore import OTSClient
from aliyun_table import TableClient
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TsMedScoreHandler(object):
    def __init__(self):
        DB_INFO = {
            'end_point':
            'https://nm-sea.cn-shenzhen.vpc.tablestore.aliyuncs.com',
            'access_key_id': 'LTAI4Fmahaa2eDwD8w8yrXY9',
            'access_key_secret': 'WiEbi6DBMwg9Vhs0V0y8yRq9B15OGu',
        }
        # self.table_cli = TableClient(instance_name='tnm-sea', **DB_INFO)
        # self.table_ots = OTSClient(instance_name='tnm-sea', **DB_INFO)
        self.table_cli = TableClient(instance_name='nm-sea', **DB_INFO)
        self.table_ots = OTSClient(instance_name='nm-sea', **DB_INFO)
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
            # news_type_id = data['news_type_id']
            # news_type_name = data['news_type_name']
            # score_data['news_types'] = json.dumps(
            #     [{"id": news_type_id,
            #       "name": news_type_name,
            #       "count": 1,
            #       }],
            #     ensure_ascii=False
            # )
            score_data['news_count'] = 0
            score_data['word_count'] = 0
            score_data['read_count'] = data['increment_read_count']
            all_read_count, news_count = self.get_news_count(medium_id)
            if news_count:
                score_data['avg_read_count'] = int(all_read_count / news_count)
            else:
                score_data['avg_read_count'] = data['increment_read_count']
            # score_data['avg_read_count'] = data['increment_read_count']
            score_data['like_count'] = data['increment_like_count']
            score_data['comment_count'] = data['increment_comment_count']
            score_data['share_count'] = data['increment_share_count']
            score_data['interact_count'] = data['increment_interact_count']
            score_data['cycle'] = scoretype
            score_data['rank_date'] = timestamp1
            now_time = int(time.time())
            score_data['created_at'] = now_time
            score_data['updated_at'] = now_time
            sta_W = 0
            sta_R = 1000 * float(
                math.log(score_data['read_count'] + 1, math.e) /
                math.log(700000 * daycount + 1.1, math.e))
            sta_Ra = 1000 * float(
                math.log(score_data['avg_read_count'] + 1, math.e) /
                math.log(100000 + 1.1, math.e))
            sta_L = 1000 * float(
                math.log(score_data['like_count'] + 1, math.e) /
                math.log(20000 * daycount + 1.1, math.e))
            sta_C = 1000 * float(
                math.log(score_data['comment_count'] + 1, math.e) /
                math.log(6000 * daycount + 1.1, math.e))
            score_data['score'] = int(sta_W * 0.1 + sta_R * 0.45 +
                                      sta_Ra * 0.2 + sta_L * 0.1 +
                                      sta_C * 0.15)
            score_data['id'] = None
            score_data['medium_id'] = medium_id
            # print(score_data)
            pk = self.table_cli.put_row(table_name='ts_medium_score',
                                        pk_list=['medium_id', 'id'],
                                        data=score_data)
            print(
                f'Write ts_medium_score succeed{pk},type:{score_data["cycle"]}.'
            )
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
        score_data[
            'read_count'] = score_data['read_count'] + data['read_count']
        if score_data['news_count']:
            score_data['avg_read_count'] = int(score_data['read_count'] /
                                               score_data['news_count'])

            # reporter = self.query_reporter(score_data['reporter_id'])
            # if not reporter:
            #     return
            # score_data['avg_read_count'] = int(score_data['read_count'] / reporter['news_count'])
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
        print(
            f'Update ts_medium_score succeed{pk},type:{score_data["cycle"]}.')
        return score_data

    def handler(self, ts_news_data):
        """
        主函数

        :return:
        """
        self.logger.info(f'媒体{ts_news_data["medium_id"]}')
        medium_id = ts_news_data['medium_id']
        # 日榜处理
        scoretype = 1
        daycount = 1
        today = datetime.date.today()
        # 当天开始时间戳
        timestamp1 = int(time.mktime(time.strptime(str(today), '%Y-%m-%d')))
        # print(timestamp1)
        # 查询该媒体是否已有日榜
        result_row = self.query_score_in_ts(medium_id, scoretype, timestamp1)
        if result_row:
            print(f'find score')
            self.update_score(result_row, ts_news_data, daycount)
        else:
            print(f'do not find score')
            self.put_score(ts_news_data, medium_id, scoretype, daycount,
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
            score_data = self.update_score(result_row, ts_news_data, daycount)
        else:
            score_data = self.put_score(ts_news_data, medium_id, scoretype,
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
            self.update_score(result_row, ts_news_data, daycount)
        else:
            self.put_score(ts_news_data, medium_id, scoretype, daycount,
                           timestamp1)

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

    def get_news_count(self, medium_id):
        all_read_count = 0
        next_token = None
        while True:
            rows, next_token, total_count, is_all_succeed = self.table_ots.search(
                'news',
                'news_index',
                ots.SearchQuery(
                    ots.BoolQuery(must_queries=[
                        ots.TermQuery('medium_id', medium_id),
                    ]),
                    get_total_count=True,
                    # offset=0,
                    sort=ots.Sort([ots.PrimaryKeySort()])
                    if not next_token else None,
                    next_token=next_token,
                    limit=100),
                ots.ColumnsToGet([], ots.ColumnReturnType.ALL))
            news_datas = self.rows_format(rows)
            for news_data in news_datas:
                # print(news_data)
                read_count = news_data.get('read_count', 0)
                all_read_count += read_count
            if not next_token:
                return all_read_count, total_count


if __name__ == '__main__':
    # ts_news_datas = [{
    #     'medium_id': 1585125575903000,
    #     'id': None,
    #     'mp_account_id': '50969479129',
    #     'mp_type_id': '1',
    #     'all_news_id': 1588047052732000,
    #     'news_id': 1585818473333000,
    #     'origin_url': 'https://www.toutiao.com/item/6804599406130627085/',
    #     'read_count': 579,
    #     'like_count': 7,
    #     'comment_count': 0,
    #     'share_count': 95,
    #     'interact_count': 7,
    #     'increment_read_count': 1,
    #     'increment_like_count': 0,
    #     'increment_comment_count': 0,
    #     'increment_share_count': 1,
    #     'increment_interact_count': 0,
    #     'reporters': '[]',
    #     'created_at': 1588047624,
    #     'updated_at': 1588047624
    # }, {
    #     'medium_id': 1585125575903000,
    #     'id': None,
    #     'mp_account_id': '50969479129',
    #     'mp_type_id': '1',
    #     'all_news_id': 1588047072884000,
    #     'news_id': 1587371184745000,
    #     'origin_url': 'https://www.toutiao.com/item/6815729589965292036/',
    #     'read_count': 420,
    #     'like_count': 1,
    #     'comment_count': 0,
    #     'share_count': 1,
    #     'interact_count': 1,
    #     'increment_read_count': 15,
    #     'increment_like_count': 11,
    #     'increment_comment_count': 10,
    #     'increment_share_count': 11,
    #     'increment_interact_count': 11,
    #     'reporters': '[{"id": 1587371188316000, "name": "蔺雪峰"}]',
    #     'created_at': 1588047625,
    #     'updated_at': 1588047625
    # }]
    ah = TsMedScoreHandler()
    # for ts_news_data in ts_news_datas:
    #     ah.handler(ts_news_data)
    #     time.sleep(5)
    all_read_count, total_count = ah.get_news_count(1583720631765000)
    print(all_read_count, total_count)
