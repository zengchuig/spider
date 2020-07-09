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


class RepScoreHandler(object):
    def __init__(self):
        # self.table_cli = aliyun_db.get_unofficial_product_cli()
        self.table_cli = aliyun_db.get_unofficial_test_cli()
        self.logger = logger

    def query_score_in_ts(self, reporter_id, scoretype, timestamp1):
        """
        查询记者是否有榜单

        :param reporter_id [int]: 记者id.
        :param timestamp1 [int]: 榜单时间戳.
        :return
        """
        must_query = [
            ('term', 'reporter_id', reporter_id),
            ('term', 'rank_date', timestamp1),
            ('term', 'cycle', scoretype),
        ]
        self.logger.info(
            f'query reporter_socre_in ts_reporter_score:{must_query}')
        sort_list = [('rank_date', -1)]
        result_iter = self.table_cli.query(
            table_name='ts_reporter_score',
            must_query_list=must_query,
            sort_list=sort_list,
            index_name='ts_reporter_score_index')
        for query_result in result_iter:
            self.logger.info(f'查到该记者的榜单')
            return query_result
        return

    def query_reporter(self, reporter_id):
        """
        查询记者
        """
        must_query = [
            ('term', 'id', reporter_id),
            ('term', 'type', 0),
        ]
        sort_list = [('created_at', -1)]
        result_iter = self.table_cli.query(table_name='reporter',
                                           must_query_list=must_query,
                                           sort_list=sort_list,
                                           index_name='reporter_index')
        for query_result in result_iter:
            self.logger.info(f'查询到该记者')
            return query_result
        return

    def put_score(self, news_data, reporter_id, scoretype, daycount,
                  timestamp1):
        """
        插入榜单
        """
        data = deepcopy(news_data)
        score_data = {}
        score_data['medium_id'] = data['medium_id']
        reporter = self.query_reporter(reporter_id)
        if not reporter:
            return
        news_types = json.loads(reporter['news_types'])
        score_data['news_types'] = json.dumps(
            sorted(news_types,
                   key=lambda news_type: news_type["count"],
                   reverse=True),
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
            math.log(2000 * daycount + 1.1, math.e))
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
        score_data['score'] = int(sta_W * 0.1 + sta_R * 0.45 + sta_Ra * 0.2 +
                                  sta_L * 0.1 + sta_C * 0.15)
        score_data['id'] = None
        score_data['reporter_id'] = reporter_id
        print(score_data)
        pk = self.table_cli.put_row(table_name='ts_reporter_score',
                                    pk_list=['reporter_id', 'id'],
                                    data=score_data)
        print(
            f'Write ts_reporter_score succeed:{pk}.type{score_data["cycle"]}')
        return score_data

    def update_score(self, result_row, data, daycount):
        """
        更新榜单
        """
        score_data = deepcopy(result_row)
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
            math.log(2000 * daycount + 1.1, math.e))
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
        score_data['score'] = int(sta_W * 0.1 + sta_R * 0.45 + sta_Ra * 0.2 +
                                  sta_L * 0.1 + sta_C * 0.15)
        print(score_data)
        pk = self.table_cli.update_row(table_name='ts_reporter_score',
                                       pk_list=['reporter_id', 'id'],
                                       data=score_data)
        print(
            f'Update ts_reporter_score succeed:{pk}.type{score_data["cycle"]}')
        return score_data

    def handler(self, all_news_data):
        """
        主函数

        :return:
        """
        reporters = json.loads(all_news_data['reporters'])
        self.logger.info('开始记者榜单计算')
        for reporter in reporters:
            self.logger.info(f'记者{reporter["name"]}')
            reporter_id = reporter['id']
            # 日榜处理
            scoretype = 1
            daycount = 1
            today = datetime.date.today()
            # 当天开始时间戳
            timestamp1 = int(time.mktime(time.strptime(str(today),
                                                       '%Y-%m-%d')))
            if int(time.time() < timestamp1 + 43200):
                # 昨天结束时间戳
                timestamp2 = int(
                    time.mktime(time.strptime(str(today), '%Y-%m-%d'))) - 1
                # 昨天开始时间戳
                timestamp1 = timestamp2 - 86399
            # 查询该记者是否已有日榜
            result_row = self.query_score_in_ts(reporter_id, scoretype,
                                                timestamp1)
            if result_row:
                self.update_score(result_row, all_news_data, daycount)
            else:
                self.put_score(all_news_data, reporter_id, scoretype, daycount,
                               timestamp1)

            # 周榜处理
            scoretype = 2
            daycount = 7
            # 一周前开始时间戳
            today = datetime.date.today()
            today = today - datetime.timedelta(days=today.weekday())
            timestamp1 = int(time.mktime(time.strptime(str(today),
                                                       '%Y-%m-%d')))
            # 查询该记者是否已有周榜
            result_row = self.query_score_in_ts(reporter_id, scoretype,
                                                timestamp1)
            if result_row:
                score_data = self.update_score(result_row, all_news_data,
                                               daycount)
            else:
                score_data = self.put_score(all_news_data, reporter_id,
                                            scoretype, daycount, timestamp1)
            # 更新记者表score
            if score_data:
                reporter_data = self.query_reporter(score_data['reporter_id'])
                if reporter_data:
                    reporter_data['score'] = score_data['score']
                    pk = self.table_cli.update_row(
                        table_name='reporter',
                        pk_list=['random_num', 'id'],
                        data=reporter_data)
                    print(f'Update reporter score succeed:{pk}.')

            # 月榜处理
            scoretype = 3
            daycount = 30
            # 一个月前开始时间戳
            today = datetime.date.today().replace(day=1)
            timestamp1 = int(time.mktime(time.strptime(str(today),
                                                       '%Y-%m-%d')))
            # 查询该记者是否已有月榜
            result_row = self.query_score_in_ts(reporter_id, scoretype,
                                                timestamp1)
            if result_row:
                self.update_score(result_row, all_news_data, daycount)
            else:
                self.put_score(all_news_data, reporter_id, scoretype, daycount,
                               timestamp1)


if __name__ == '__main__':
    all_news_data = {
        'medium_name': '光明日报',
        'medium_id': 1583720629939000,
        'title': '全国超1亿学生复课，校园防疫怎么做？',
        'content':
        '<article><div class="pgc-img"><img src="http://p1.pstatp.com/large/pgc-image/0b070d3f37914906a6a03d06501be508.png" width="640" height="428" thumb_width="120" thumb_height="80"   ></img><p class="pgc-img-caption"></p></div><p>5月12日，教育部召开新闻发布会。会上，应对新冠肺炎疫情工作领导小组办公室主任、 体育卫生与艺术教育司司长王登峰介绍，目前全国复课学生总数已超1亿，接近学生总数的40%。</p><p><strong>全国超1亿学生复课，占比接近40%</strong></p><p>王登峰介绍，截至5月11日，目前开学已经复课的学生总数是10779.2万，超过了1个亿，占学生总数的39%，接近40%。</p><p>其中，高校大学生是<strong>290.7万</strong>，包括26个省（区、市）和新疆生产建设兵团，都已经部分高校开学，目前高校还没有开学的只剩下五个省，即北京、河北、山东、湖北和黑龙江；高中已经返校的学生<strong>2161.5万</strong>人，这是所有省（区、市）和兵团都已经开学了；中职已经返校<strong>327万</strong>，包括24个省（区、市）和新疆生产建设兵团；初中已经返校<strong>3148万</strong>，包括29个省（区、市）加新疆生产建设兵团；小学已经返校<strong>4384.4万</strong>，包括了21个省（区、市）和新疆生产建设兵团；幼儿园已经有8个省（区、市）开园，返园的幼儿有<strong>468万</strong>。这样合在一块儿，就是1.07亿学生已经返校。</p><p><strong>教育系统还有1位确诊病例，</strong></p><p><strong>14位无症状感染者</strong></p><p>王登峰介绍，教育系统疫情的情况，目前整个教育系统2.78亿学生加上1700万教职工里面，还有1位确诊病例，目前还在进行医学观察的无症状感染者有14人。确诊病例还有1个，这是黑龙江省境外输入的关联病例。</p><p>教育系统有境外输入病例43例，目前已经全部治愈出院。</p><p><strong>校园疫情防控做好六方面工作</strong></p><p>王登峰表示，就目前来讲，教育系统疫情防控的总体形势，就是要在常态化下，毫不放松地做好校园疫情防控工作。因此下一步主要做好六个方面的工作：</p><p><strong>一是精准分类。</strong>所谓精准分类，就是对海外回国人员、治愈出院人员、无症状感染者和高风险地区人员要做到精准分类，确保开学以后进入校园的每一个人都是健康的。</p><p><strong>二是细化开学和防控的措施。</strong>从开学以后，从校园里面的体育活动、佩戴口罩，以及教室、宿舍、食堂、操场、活动场所、校园的医务室，以及学生上下学的过程和师生的接触史，都要细化各项防控措施，而且要尽快建立和完善师生健康状况日报告制度和出现缺课缺勤的跟踪制度，包括如何最大限度地让学生能够返校，还要满足防控的要求。</p><p><strong>三是强化条件保障，要备足防疫物资。</strong></p><p><strong>四是要做出快速反应。</strong>我们所采取的各项措施，目标是要做到万无一失，但是同时在确保万无的基础上，还要保障一旦有一失能够快速应对，形成闭环，能够及时处置，快速处置，这也是我们现在做好复学工作的一个非常重要的方面。</p><p><strong>五是加强培训。</strong>对教育行政人员、对校园的医护人员、对广大师生和家长，加强卫生防疫方面的培训，特别是跟疫情防控相关的一系列工作。</p><p><strong>六是关怀和帮助。</strong>要努力对广大师生在复学后进行思想引导，学业和就业方面的指导，以及心理疏导和人文关怀，确保校园安全稳定，确保开学复学工作安全有序。</p><p><strong>安全第一！</strong></p><p><strong>校园防疫不能松懈！</strong></p><p><br></p><hr><p>内容：教育部官网、光明微教育（统筹：唐芊尔）</p></article>',
        'origin_url': 'https://www.toutiao.com/item/6825841970552766990/',
        'edition': '',
        'mp_account_id': 1584512406861000,
        'mp_account_name': '光明日报',
        'mp_article_id': '6825841970552766990',
        'mp_type_id': 1,
        'mp_type_name': '今日头条',
        'published_at': 1589265179,
        'read_count': 7,
        'like_count': 0,
        'comment_count': 0,
        'share_count': 0,
        'wx_comment_id': 0,
        'cover_img':
        'http://p1.pstatp.com/large/pgc-image/0b070d3f37914906a6a03d06501be508.png',
        'news_id': 1589268574953000,
        'tags': '["王登峰"]',
        'tencent_type1': '教育',
        'tencent_type2': '高等教育',
        'news_type_id': 14,
        'news_type_name': '教育',
        'abstract':
        '5月12日，教育部召开新闻发布会。会上，应对新冠肺炎疫情工作领导小组办公室主任、 体育卫生与艺术教育司司长王登峰介绍，目前全国复课学生总数已超1亿，接近学生总数的40%。全国超1亿学生复课，占比接近4',
        'word_count': 1176,
        'interact_count': 0,
        'reporters': '[{"id": 1589268579050000, "name": "唐芊尔"}]',
        'cont_start': '5月12日，教育部召开新闻发布会。会上，应对新冠肺炎疫情工作领导小组办公室主任、 体育卫生与艺术教育',
        'cont_end': '松懈！内容：教育部官网、光明微教育（统筹：唐芊尔）',
        'other_status': 0,
        'reprinted_status': 0,
        'reprint': '{"type": 0, "list": []}',
        'created_at': 1589268575,
        'updated_at': 1589268575,
        'reprint_from': '[]'
    }
    ah = RepScoreHandler()
    ah.handler(all_news_data)
