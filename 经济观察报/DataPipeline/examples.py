"""
Examples of request and reponse.
"""
title = ''
content = ''
with open('example_article.txt', 'r',encoding='utf-8') as f:
    for i in f.readlines():
        if not title:
            title = i
            continue
        content += i

CATEGORIES_REQUEST_EXAMPLE = {
    'content': content,
}

TAGS_REQUEST_EXAMPLE = {
    'title': '闻客:致力于解决作者写作痛点开启写作新模式',
    'content': content,
}


REPORTERS_REQUEST_EXAMPLE = {
    'content': content,
}


ARTICLE_PIPELINE_EXAMPLE = {
    "medium_name": "长寿日报",
    "medium_id": 1583720629643000,
    "title": "中国邮政集团有限公司党组公布对26家邮政企业单位巡视反馈情况",
    'content': '本报讯（记者曹丽华）阳文彬是云台镇综合执法大队干部，蒋佳玮是云台镇产业发展服务中心干部，从2月21日开始，他们又有另一个身份---企业复工复产驻厂督导员。在云台镇像阳文彬这样的督导员有13人，他们每天在辖区13个企业里，开展一对一上门服务。经过10多天的携手战疫，企业对他们的工作高度认可，称他们不仅是企业复工复产督导员，还是企业安全生产的定心丸。3月4日早上，阳文彬来到大田粮油加工厂，开启了新一天的工作：从检查企业门岗对出入厂区人员体温检测、登记开始，查看企业消毒记录、观察日志记录情况，监督企业是否进行疫情防控知识培训、是否实行分时分餐制、职工是否戴口罩等，每一个环节、每一个细节，阳文彬都不放过。有了他们的指导，我们企业安全生产的‘弦’绷得更紧了！大田粮油加工厂相关负责人说。蒋佳玮是万顺木材加工厂的驻厂督导员，他的另一个职责是推动企业加快有序复工复产进度。为此，他还指导和服务企业做好复工复产报备表、疫情防控承诺书等备案工作，深入了解企业生产运营情况，积极帮助企业解决实际困难。最近口罩不好买，我们想储备得更充足一些，你们能不能帮我们想点法子？万顺木材厂负责人杨明星提出了这样的诉求。放心，我们尽快给你们想办法！蒋佳玮第一时间向镇领导汇报，通过多渠道发力，帮助企业协调到一批口罩，解了燃眉之急。目前，云台镇的这些驻厂督导员仍奔波在一线，当好企业的宣传员、服务员，为企业解决防疫物资储备、原材料供应、市场销售等实际困难，有序推进企业复工复产。',
    "origin_url": "http://epaper.ccs.cn/pad/202003/09/c11337.html",
    "edition": "02",
    "mp_account_id": 112,
    "mp_account_name": "长寿日报",
    "mp_type_id": 1,
    "mp_article_id": "12da3fb3c2345",
    "mp_type_id": 1,
    "mp_type_name": '今日头条',
    "published_at": 1583828338,
    "read_count": 100,
    "like_count": 12,
    "comment_count": 3,
    "share_count": 1,
  }

USER_PIPELINE_EXAMPLE = {
    'medium_name': '财新',
    'medium_id': 123,
    'mp_type_id': 1,
    'mp_type_name': '今日头条',
    'mp_user_name': '财新网',
    'mp_user_id': '1a3f92a3bc',
    'logo': 'https://gw.alipayobjects.com/zos/rmsportal/XuVpGqBFxXplzvLjJBZB.svg',
    'intro': '用户介绍',
    'fans_count': 100,
}

