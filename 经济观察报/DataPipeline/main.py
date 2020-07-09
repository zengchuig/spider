from fastapi import FastAPI, Query, Body
from pydantic import BaseModel, Field
from modules import (calc_category, calc_keywords, extract_reporters,
                     extract_correspondents, map_internal_category)
from models import (CategoriesResponseItem, TagsResponseItem, CategoriesItem,
                    CategoriesInputItem, TagsInputItem, NewUserTaskInputItem,
                    ArticlePipelineInputItem, ReportersInputItem,
                    UserCorrelationInputItem, UserPipelineInputItem)
from db.user_handler import UserHandler
from db.article_handler import ArticleHandler
from examples import (CATEGORIES_REQUEST_EXAMPLE, TAGS_REQUEST_EXAMPLE,
                      REPORTERS_REQUEST_EXAMPLE, ARTICLE_PIPELINE_EXAMPLE,
                      USER_PIPELINE_EXAMPLE)
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(host='0.0.0.0')
user_handler = UserHandler()
article_handler = ArticleHandler()


# @app.get("/article/categories", response_model=CategoriesResponseItem)
# def get_article_categories(item: CategoriesInputItem = Body(
#     ..., example=CATEGORIES_REQUEST_EXAMPLE)):
#     content = item.content
#     # task = calc_category.delay(content)
#     # category = task.get(timeout=5)
#     category = calc_category(content)
#     first_level_category, second_level_category = category
#     print('-' * 100)
#     print(category)
#     news_type_id, news_type_name = map_internal_category(first_level_category)
#     category_item = CategoriesItem(first_level_category=first_level_category,
#                                    second_level_category=second_level_category,
#                                    news_type_id=news_type_id,
#                                    news_type_name=news_type_name)
#     print(dict(category_item))
#     return CategoriesResponseItem(message='success', category=category_item)


# @app.get("/article/tags", response_model=TagsResponseItem)
# def get_article_tags(item: TagsInputItem = Body(...,
#                                                 example=TAGS_REQUEST_EXAMPLE)):
#     title = item.title
#     content = item.content
#     logger.info(f'title:{title}')
#     logger.info(f'content:{content}')
#     # task = calc_keywords.delay(title, content)
#     # tags = task.get(timeout=5)
#     tags = calc_keywords(title, content)
#     #return ','.join(tags)
#     print(tags)
#     return TagsResponseItem(message='success', tags=tags)


# @app.get("/article/reporters")
# def get_article_reporters(item: ReportersInputItem = Body(
#     ..., example=REPORTERS_REQUEST_EXAMPLE)):
#     """Get article reporters."""
#     content = item.content
#     reporters = extract_reporters(content)
#     print(reporters)
#     return {'reporters': reporters}


# @app.get("/article/correspondents")
# def get_article_reporters(item: ReportersInputItem = Body(
#     ..., example=REPORTERS_REQUEST_EXAMPLE)):
#     """Get article reporters."""
#     content = item.content
#     correspondents = extract_correspondents(content)
#     print(correspondents)
#     return {'correspondents': correspondents}


@app.post("/article")
#def save_articles(item:ArticlePipelineInputItem=Body(..., example=ARTICLE_PIPELINE_EXAMPLE)):
def save_articles(item: ArticlePipelineInputItem):
    title = item.title
    global article_handler
    article_handler.write_article(dict(item))
    return {'message': 'success'}


@app.post("/account")
def save_media_platform_user_infomation(item: UserPipelineInputItem = Body(
    ..., example=USER_PIPELINE_EXAMPLE)):
    global user_handler
    user_handler.write_user(dict(item))
    return {'message': 'success'}


# @app.put("/spider/mp_account/correlation")
# def associated_media_and_media_platform_accounts(
#     item: UserCorrelationInputItem = Body(..., )):
#     # 新的关联信息
#     print(dict(item))
#     return {'message': 'success'}


# @app.post("/spider/task/media")
# def new_media(item: NewUserTaskInputItem = Body(..., )):
#     # 新的关联信息
#     print(dict(item))
#     return {'message': 'success'}
