"""
Definitions of request and response items.
"""
from typing import List
from pydantic import BaseModel, Field


class CategoriesInputItem(BaseModel):
    content: str = Field(
        ...,
        title='Content of aritcles.',
        description='Please remove HMTL tags in content \
                                      before calculate tags.',
        min_length=1,
        max_length=10000)


class TagsInputItem(BaseModel):
    title: str = Field(
        ...,
        title='Title of aritcles.',
        description='Title must be not null and shorter \
                                    than 40',
        min_length=1,
        max_length=40)
    content: str = Field(
        ...,
        title='Content of aritcles.',
        description='Please remove HMTL tags in content \
                                      before calculate tags.',
        min_length=1,
        max_length=10000)


class ReportersInputItem(BaseModel):
    content: str = Field(
        ...,
        title='Content of aritcles.',
        description='Please remove HMTL tags in content \
                                      before calculate tags.',
        min_length=1,
        max_length=10000)


class CategoriesItem(BaseModel):
    first_level_category: str = Field(..., title='腾讯一级分类', example='科技')
    second_level_category: str = Field(..., title='腾讯二级分类', example='创投')
    news_type_id: str = Field(..., title='新闻类型id (内部)', example='')
    news_type_name: str = Field(
        ...,
        title='新闻类型名 (内部)',
        description=
        '腾讯分类和内部分类对应关系: https://www.yuque.com/waykey/product/bdwrdn?inner=tcUSE',
        example='创投')


class CategoriesResponseItem(BaseModel):
    message: str = Field(...,
                         example='success',
                         title='Response message',
                         min_lenth=1,
                         max_length=40)
    category: CategoriesItem = Field(..., title='Category of the article.')


class TagsResponseItem(BaseModel):
    message: str = Field(...,
                         example='success',
                         title='Response message.',
                         min_lenth=1,
                         max_length=40)
    tags: List[str] = Field(..., example=['时政'], title='Tags of the article.')


class ReportersResponseItem(BaseModel):
    message: str = Field(...,
                         example='success',
                         title='Response message.',
                         min_lenth=1,
                         max_length=40)
    reporters: List[str] = Field(...,
                                 titie='Reporters name list.',
                                 example=['张三', '李四'])


class ArticlePipelineInputItem(BaseModel):
    medium_name: str = Field(..., title='媒体名', example='test')
    medium_id: int = Field(..., title='媒体id', example='999')
    title: str = Field(..., title='文章标题', example='文章标题')
    content: str = Field(..., title='文章内容')
    origin_url: str = Field(..., title='文章链接')
    edition: str = Field('', title='新闻版面号', description='新闻所在版本号, 没有可以不传')
    mp_account_id: int = Field(..., title='平台账号id (内部)')
    mp_account_name: str = Field(..., title='平台账号名')
    mp_article_id: str = Field(..., title='平台文章id')
    mp_type_id: int = Field(..., title='平台id (内部)')
    mp_type_name: str = Field(..., title='平台名 (内部)')
    published_at: int = Field(..., title='发布时间')
    read_count: int = Field(0, title='阅读数')
    like_count: int = Field(0, title='点赞数')
    comment_count: int = Field(0, title='评论数')
    share_count: int = Field(0, title='分享数')
    wx_comment_id: int = Field(0,
                               title='微信评论id',
                               description='微信公众号爬虫需要多增加这个字段, 没有可以不传')
    cover_img: str = Field('', title='封面图片', description='文章的封面图片, 没有可以不传')
    is_free: int = Field(1, title='是否免费文章', description='标记文章的全文是否免费, 没有可以不传')
    reporter_name_list: List[str] = Field([],
                                          title='记者名列表',
                                          description='其他平台的记者名列表, 没有可以不传')
    reporter_source: str = Field('',
                                 title='记者名所在处',
                                 description='记者名所在处, 没有可以不传')
    ori_medium_name: str = Field('',
                                 title='原创媒体名',
                                 description='原创媒体名, 没有可以不传')
    reporter_data: dict = Field(
        {},
        title='记者其他信息',
        description='其他平台的记者信息, 没有可以不传',
        example=
        '{"medium_reporter_id":"123","avatar":"a.png","introduction":"简介","post":"职位","wechat":"weixin123","email":"123@qq.com"}'
    )


class UserPipelineInputItem(BaseModel):
    medium_name: str = Field(..., title='媒体名', example='人民日报')
    medium_id: int = Field(..., title='媒体id')
    mp_type_id: int = Field(..., title='平台id (内部)')
    mp_type_name: str = Field(..., title='平台名称 (内部)')
    mp_user_name: str = Field(..., title='该平台用户名')
    mp_user_id: str = Field(..., title='该平台用户id')
    mp_user_medium_id: str = Field('', title='该平台媒体id(外部),没有不传')
    logo: str = Field(..., title='该平台用户头像')
    intro: str = Field(..., title='该平台用户简介')
    fans_count: int = Field(..., title='该平台用户粉丝数')


class UserCorrelationInputItem(BaseModel):
    medium_name: str = Field(..., title='媒体名', example='人民日报')
    medium_id: int = Field(..., title='媒体id')
    mp_type_id: int = Field(..., title='平台id (内部)')
    mp_type_name: str = Field(..., title='平台名称 (内部)')
    mp_user_name: str = Field(..., title='该平台用户名')
    mp_user_id: str = Field(..., title='该平台用户id')
    mp_user_medium_id: str = Field('', title='该平台媒体id(外部),没有不传')


class NewUserTaskInputItem(BaseModel):
    medium_name: str = Field(..., title='媒体名', example='人民日报')
    medium_id: int = Field(..., title='媒体id')
