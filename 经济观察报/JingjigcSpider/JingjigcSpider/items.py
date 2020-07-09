# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class ArticleItem(Item):
    """ 文章信息 """
    medium_id = Field()
    medium_name = Field()
    mp_account_id = Field()
    mp_account_name = Field()
    mp_type_id = Field()
    mp_type_name = Field()

    mp_article_id = Field()  # 文章id
    title = Field()  # 文章标题
    content = Field()  # 文章内容
    origin_url = Field()  # 文章URL
    published_at = Field()  # 文章发表时间
    read_count = Field()  # 阅读数
    like_count = Field()  # 点赞数
    share_count = Field()  # 转发数
    comment_count = Field()  # 评论数
    cover_img = Field()  # 封面图
    is_free = Field()  # 是否免费
    reporter_name_list = Field()  # 记者名列表
    reporter_source = Field()  # 记者名所在字符串
    ori_medium_name = Field()
