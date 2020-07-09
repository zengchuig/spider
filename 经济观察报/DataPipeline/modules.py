
# -*- coding: utf-8 -*-
import random
import re
import time
from threading import Thread
import logging
# import pyhanlp
# from aip import AipNlp
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.nlp.v20190408 import nlp_client, models
import aliyun_db
from tablestore.metadata import *
import time
from aip import AipNlp
from html.parser import HTMLParser

#游璇钰  涂坚  宗兆洋  骆志雄   翟亚男  旦增西旦 滕朝  安娜 农超武 窦晓星
surname_pattern = r'[傅冉车凌齐耿易牟臧佟祁柴涂宗骆王李古张刘陈翟杨裴黄赵周吴徐阮凤胥邬乔孙马狄胡靳朱柯郭何罗章殷聂申宁詹梅高倪奚颜林盛郑柳纪岳梁谢唐许安冯宋韩邓彭曹曾田于肖苗潘袁董叶杜丁蒋程余吕旦房边滕葛' \
                  r'魏蔡苏任卢沈姜姚钟崔陆谭汪石付贾范金方韦夏廖侯白孟邹秦尹江熊薛农邱闫段雷季史陶毛贺万顾关郝孔向龚邵钱武扬' \
                  r'黎汤戴严文常牛莫洪米康温代赖施覃安][\u4e00-\u9fa5]{1,3}$'

compound_pattern = r'欧阳|上官|皇甫|司徒|令狐|诸葛|司马|宇文|申屠|南宫|夏侯|张孙|' \
                   r'罕古|古丽|热娜|玛依|阿依|阿里|艾伯|艾克|古兰|乌图|多里|阿不|迪丽|多吉|边巴'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# app_id, app_key, secret_key
BAIDU_KEY_LIST = [
    ('18171124', '',
     ''),
]

# Tencent cloud credential list.
# secretId，secretKey
TENCENT_KEY_LIST = [
    ("",
     ""),
]


def calc_keywords(title: str, content: str) -> str:
    """
    Calculate keywords by using baidu nlp.
    Baidu-nlp limitation:
        - Content length limit is 21k.
        - Title length limit is 40.
        - Empty title is invalid.
        - QPS: 5
    :param title: Article title.
    :param title: Article content.
    :return: tags of article if get kewords succeed, else empty string.
    """
    logging.info(f'modules.py:{title}:{content}')
    # Remove spaces and html tas.
    content = clear_all_html(content)
    # Limit length.
    content = content[:20000]
    title = title[:40]
    # Make sure title is not empty.
    if not title:
        title = content[:10]
    # Avoiding coding problems.
    content = content.encode('gb18030', 'ignore').decode('gbk', 'ignore')
    for i in range(5):
        try:
            # Tring to get keywords.
            app_id, api_key, secret_key = random.choice(BAIDU_KEY_LIST)
            client = AipNlp(app_id, api_key, secret_key)
            result = client.keyword(title, content)
            # Handle error.
            if result.get('error_code'):
                return ''
            # Get result.
            items = result.get('items')
            a = [i['tag'] for i in items]
            return a
        except Exception as e:
            time.sleep(1)
    return []


def translate(str):
    line = str.strip()  # 处理前进行相关的处理，包括转换成Unicode等
    pattern = re.compile('[^\u4e00-\u9fa50-9]')  # 中文的编码范围是：\u4e00到\u9fa5
    zh = " ".join(pattern.split(line)).strip()
    # zh = ",".join(zh.split())
    outStr = zh  # 经过相关处理后得到中文的文本
    return outStr


def calc_category(content):
    """
    Calculate category by using tencent nlp.
    Tecent api limitation:
        - Content length: 10k.
        - Empty String is invalid.
        - QPS:20
    """
    # Data pre-handle.
    content = clear_all_html(content)
    content = content[:10000]
    content = content.strip('\n').strip()
    content = translate(content)
    # Get categor
    secret_id, secret_key = random.choice(TENCENT_KEY_LIST)
    cred = credential.Credential(secret_id, secret_key)
    httpProfile = HttpProfile()
    httpProfile.endpoint = "nlp.tencentcloudapi.com"
    clientProfile = ClientProfile()
    clientProfile.httpProfile = httpProfile
    client = nlp_client.NlpClient(cred, "ap-guangzhou", clientProfile)
    for i in range(5):
        try:
            req = models.TextClassificationRequest()
            params = '{"Flag":2,"Text":"' + content + '"}'
            req.from_json_string(params)
            resp = client.TextClassification(req)
            return resp.Classes[0].FirstClassName, resp.Classes[
                0].SecondClassName
        except Exception as e:
            print(f'分类错误: {e}')
            time.sleep(1)
            return '', ''


#  阿里云人名判断
def get_chinese_name(text):
    """
        :param text: 中文字符串
        :return: 人名
        """
    """识别人名"""
    # 上一步获取到的ID AK SK
    APP_ID = '18171124'
    API_KEY = 'fmFXS6iGGt6icgiE1B9OTzyj'
    SECRET_KEY = 'UcCHHlEnYNRZCyowyCuBrfCWy4ISvf4B'

    client = AipNlp(APP_ID, API_KEY, SECRET_KEY)

    text = str(text.encode('gbk', 'ignore'),
               encoding='gbk')  # ignore忽略无法编码的字符,如果不加这个会报错。

    # 设置请求间隔,免费版的QPS限制为2,有能力的可以购买。
    time.sleep(1)

    # 调用词法分析的返回结果
    # print(client.lexer(text))
    """ 调用词法分析 """
    try:
        for i in client.lexer(text)['items']:
            # 若字符串中有人名就返回人名
            if i['ne'] == 'PER':
                # return i['item']
                return text.replace('丨', '')
    except:
        pass
    return ''


# 提取记者名main
# def extract_reporters(text):
#     raw_text = clear_all_html(text)
#     if len(raw_text) > 150:
#         new_text = raw_text[:100] + raw_text[-50:]
#     else:
#         new_text = raw_text
#
#     # 保存最终返回的记者列表
#     res = []
#
#     # 不经过 NLP
#     res = get_reporter_list_1(clear_html_for_reporter(text))
#     # 阿里云人名判断
#     res = [get_chinese_name(str(r)) for r in res]
#     if res:
#         return res
#
#     # 在前100行和后50行抽取记者
#     print(new_text)
#     name_str_list = extract_reporter_name_strings(new_text)
#     for name_str in name_str_list:
#         name_list = extract_reporter_from_string(name_str)
#         res.extend(name_list)
#     res = list(set(res))
#
#     # 正则抽取到记者后，用 NLP 判断是不是人名
#     if res:
#         temp_list = []
#         for name_str in res:
#             temp_list.extend(get_namelist_from_hanlp(name_str))
#         res = list(set(temp_list))
#
#     if not res:
#         # 正则抽取不到记者，就全文抽取，重复上面步骤
#         name_str_list = extract_reporter_name_strings(raw_text)
#         for name_str in name_str_list:
#             name_list = extract_reporter_from_string(name_str)
#             res.extend(name_list)
#         res = list(set(res))
#
#         if res:
#             temp_list = []
#             for name_str in res:
#                 temp_list.extend(get_namelist_from_hanlp(name_str))
#             res = list(set(temp_list))
#
#     # 阿里云人名判断
#     res = [get_chinese_name(str(r)) for r in res]
#     if res:
#         return res


# 含有记者名字段
def get_reporter_list(text_str):
    pattern_list = [
        re.compile(
            # 媒体 实习 朝阳报 全媒 特约 每经 新闻 半岛 南京 本刊  首席 长沙报道  特派 联合报道组
            r'(?<=[体习报约岛京网媒端派频末组讯闻经刊席\s）（\(\u0001])(?<!，。)[记作][\u0001\s]{0,3}?者(?!简介|发现|进|见|加|已|说|，在|“|编辑)(.{2,35}?)(?=[\)（）责编等\-著图\n\u3000]|文 |文/图|文中|来源|本报|长沙|重庆|运营|整理|报道|主编|评论|见习|制作|实习|策划|制图|采访|通讯|摄影|每经|校对|监制|海报|视频|\u0001$)',
            re.S),
        re.compile(r'.记者(.{2,6}?)(?=通讯|编辑)'),
        re.compile(r'来源：记者(.{2,10}?)通讯员'),
        re.compile(r'实习[生]*(.{2,10}?)[\u0001通校]'),
        re.compile(r'[^“材片]来源：.{0,10}?报[\u0001记者]*(.{2,16}?)[制作\u0001]'
                   ),  # 来源：孝感日报 张三 李斯 王五
        re.compile(r'记者(.{1,8}?)文/摄'),  # 全媒体记者 王吉奇 文/
        re.compile(r'记者(.{1,8}?)文/图'),
        re.compile(r'文/(.{0,10}?)(?=[图/\u0001（])'),  # 文/张翔  文/付彪 图/新华社发 朱慧卿作
        re.compile(r'文 [\|丨] (.{0,20}?)(?=[图/\u0001])'),  # 文 | 张晓 黎明 石田经
        re.compile(r'文丨(.{0,4}?)\u0001'),
        re.compile(r'文\u0001[\|丨](.{0,10}?)\u0001'),
        re.compile(r'\u0001记者(.{,6}?)\u0001'),
        re.compile(r'记者(.{2,10}?)[\n校]'),
        re.compile(r'[记作]者 [\|丨](.{2,10}?)\u0001'),
        re.compile(
            r'记者\u0001\n(.{2,50}?)\n'
        ),  # \x01作者 | 中青报·中青网记者\x01\n            \x01王鑫昕 朱彩云 刘世昕 胡春艳\x01\n
        re.compile(
            r'（.{0,10}?记者(.*?)）'
        ),  # （新甘肃·甘肃日报记者 王睿君 严存义 杜雪琴 洪文泉 薛砚 顾丽娟 崔银辉 李欣瑶 秦娜）为什么要分离出来，如果写在第一个规则里面担心对全局有影响
        re.compile(r'\u0001作者：(.{2,10}?)                  \u0001来源'),
        re.compile(r'\u0001(.{0,3}?)\u0001编辑'),
        re.compile(r'\u0001(.{0,10}?)/文[ \u0001]'),
        re.compile(r'文/记者(.{0,3}?)图/'),
        re.compile(r'文/图(.{0,3}?)[\u0001编]'),
        re.compile(r'文图/记者\u0001(.{0,3}\u0001)'),
        re.compile(
            r'(?<=[体习报约岛京网媒端派频闻经刊席\s）（\(\u0001])(?<!，。)记者(.{0,10}?)[\u0001校\)）】]'
        ),
        re.compile(r'\x01[本文]*作者：(.{0,6}?)\x01'),
        re.compile(r'  记者(.{0,6}?)\s{1,5}'),
        re.compile(r'\u0001文[字]* [\|丨]\u0001(.*?)\u0001'),
        re.compile(r'\u0001文\u0001[\|丨] \u0001(.*?)\u0001'),
        re.compile(r'记者\s{0,3}?(.{0,10})$'),  #前方数据
        #re.compile(r'[■□●]\s{0,2}?(.{2,10}?)[\r\n\u3000]'),
        re.compile(r'报讯[\(（](.{0,10}?)[报)）]'),
        re.compile(r'记者(.{2,5}?) ')
    ]

    temp_list = []
    for pattern in pattern_list:
        extract_str = re.findall(pattern, text_str)
        extract_str = list(filter(lambda i: "院" not in i,
                                  extract_str))  # （作者：陈甦，系中国社会科学院学部委员、法学研究所所长）
        extract_str = list(filter(lambda i: "摄" not in i,
                                  extract_str))  # '记者 程敏 摄\x01\x01  记者 张晓东摄
        extract_str = list(filter(lambda i: "图" not in i, extract_str))
        extract_str = list(filter(lambda i: "供" not in i,
                                  extract_str))  #记者：xx供图
        extract_str = list(filter(lambda i: "编辑" not in i, extract_str))
        extract_str = list(filter(lambda i: "通讯" not in i, extract_str))
        extract_str = list(filter(lambda i: "报" not in i, extract_str))
        extract_str = list(filter(lambda i: "“" not in i, extract_str))
        extract_str = list(filter(lambda i: "签发" not in i, extract_str))
        extract_str = list(filter(lambda i: "整理" not in i, extract_str))
        extract_str = list(filter(lambda i: "《" not in i, extract_str))
        temp_list.extend(extract_str)
    # 去重后的字段
    temp_list = list(set(temp_list))
    s = set()
    for temp in temp_list:
        # 对两个字 分开的名字进行拼接
        if len(temp.replace(' ', '').replace('\u0001', '')) == 2:  # ' 刘 睿'
            temp = temp.replace(' ', '').replace('\u0001', '')
            if get_chinese_name(temp):
                temp = temp
        if '·' in temp and not temp.startswith('·') and not temp.endswith(
                "·"
        ) and '记' not in temp and '报' not in temp:  # (作者比尔·巴尔特，陈俊安译)
            temp = temp.strip().strip('：').strip('\u0001').strip('|').strip(
                "）")
            temp = temp.split('，')[0]
            s.update([temp])
            continue
        extract_zh = re.findall(r"([\u4e00-\u9fa5]+)", temp.replace(
            "丨", ''))  # '：梁&nbsp; &nbsp; 晴\x01\x01\x01\x01\x01\x01'
        if len(extract_zh) == 2 and len(extract_zh[1]) == 1 and len(
                extract_zh[0]) == 1:
            extract_zh = ''.join(extract_zh)
            if get_chinese_name(extract_zh):
                extract_zh = [extract_zh]

        if extract_zh:
            extract_zh = set(extract_zh)
            s.update(extract_zh)
    result = list(s)
    if result:
        # index_len = len(result)
        # result = [result[i] for i in range(index_len) if 1 < len(result[i]) < 5 or "·" in result[i]]
        result = list(
            filter(lambda rst: 1 < len(rst) < 5 or "·" in rst, result))
        tmp_result = result[:]
        filter_words = [
            '到', '据', '这', '在', '村', '到', '译', '答', '个', '次', '着', '亡', '像', '侮',
            '的', '网', '近', '试', '前', '译', '再', '我', '说', '报', '眼', '哥', '鸭','辆',
            '街', '省', '站长', '看到', '吐露', '昨日', '日前', '近日', '试行', '青岛', '小雨','凌晨',
            '从中', '发布', '查阅', '平均', "成都", '查询', '记者', '老师', '常年', '供应', '手记',
            '昨日', '项目', '解释', '华东', '开始', '现场', '郑州', '挥手', '配送', '得知', '支付',
            '中介', '报道', '文章', '现场', '耳中', '中国', '旅游', '登录', '中国', '介绍', '综合',
            '这段', '调查', '问及', '科技', '投诉', '回忆', '市民', '暗访', '疫苗', '合肥', '天才',
            '透露', '背后', '荆州', '发现', '简介', '单位', '董事长', '股份', '方面', '致电', "口罩",
            "洗手", "消毒", '了解', '反映', '受访', '健康', '人山', '走访', '道德', '主任', '采写',
            '打击', '新闻', '天气', '重庆', '文字', '文明', '房产', '校长', '图片', '表示', '刚刚',
            '整理', '采访', '奔赴', '标题', '平日', '奉献', '一线', '行长', '期间', '日至', '注意',
            '知情', '西路', '济南', '中电', '强调', '青岛', '手记', '武汉', '视频', '信息', '女士',
            '先生', '谢谢', '踊跃', '北京', '上海', '广州', '万元', '合计', '日摄', '内容', '联系',
            '询问', '东路', '过去', '观察', '关注', '分析', '从中', '获悉', '格力', '地产', '深圳', '记者',
            '走出', '众志', '难攻', '石家', '纪念'
        ]

        for r in tmp_result:
            for i in filter_words:
                if (i in r or
                    (len(r) <= 3 and not re.match(surname_pattern, r)) or
                    (4 <= len(r) <= 6 and
                     not re.match(compound_pattern, r[:2]))) and ('·'
                                                                  not in r):
                    try:
                        result.remove(r)
                        break
                    except:
                        continue

        result = ' '.join(result).split()
        result = list(
            filter(lambda i: i and len(i) < 11 and '[' not in i,
                   result))  # [英]罗伯特·斯基德尔斯基

        if not result:
            return []
    # logger.info(f"提取到的记者:{result}")
    return result


# 没有记者名字段的提取
def get_reporter_excpt_list(text_str):
    '''
        匹配没有 “作者” 字段的数据  其中包括（） 或者没有括号的数据
        提取括号里的姓名 用nlp识别是否是人名
        带括号和没带括号，确实是记者名的一般出现在头尾
        '''
    pattern_list = [
        re.compile(r'[^\d\w]*[\(（]([^\d]*.{2,15}?)[\)）](?=[^\d\w]|$)'),
        re.compile(r'^\u0001(.{0,10}?)(?=[。编审]|\u0001)'
                   ),  # \x01中国基金报 莫飞\x01  #'\x01万卫星，1958年7月生于湖北天  ，
        re.compile(r'[^辑]\u0001(.{0,10})\u0001$'),
        re.compile(r'^\u0001.{0,7}?报(.{0,6})\u0001'),
        re.compile(r'[■□●]\s{0,2}?(.{2,10}?)[\r\n\u3000]'),
    ]

    temp_list = []
    for pattern in pattern_list:
        extract_str = re.findall(pattern, text_str)
        extract_str = list(filter(lambda i: "摄" not in i, extract_str))
        extract_str = list(filter(lambda i: "图" not in i, extract_str))
        extract_str = list(filter(lambda i: "编" not in i, extract_str))
        extract_str = list(filter(lambda i: "院" not in i,
                                  extract_str))  # 山东中医药大学附属医院-苏斌
        extract_str = list(filter(lambda i: "审" not in i,
                                  extract_str))  # 山东中医药大学附属医院-苏斌
        extract_str = list(filter(lambda i: "通讯" not in i,
                                  extract_str))  #（编辑：王洽） ['编审 廖波']
        extract_str = list(filter(lambda i: "编辑" not in i, extract_str))
        extract_str = list(filter(lambda i: "监制" not in i,
                                  extract_str))  #['监制:吴秋艳']
        extract_str = list(filter(lambda i: "校对" not in i, extract_str))
        extract_str = list(filter(lambda i: "签发" not in i, extract_str))
        extract_str = list(filter(lambda i: "视觉" not in i, extract_str))
        extract_str = list(filter(lambda i: "统筹" not in i, extract_str))
        extract_str = list(filter(lambda i: "策划" not in i, extract_str))
        extract_str = list(filter(lambda i: "制作" not in i, extract_str))
        extract_str = list(filter(lambda i: "整理" not in i, extract_str))
        extract_str = list(filter(lambda i: "值班" not in i, extract_str))
        extract_str = list(filter(lambda i: "《" not in i, extract_str))
        extract_str = list(filter(lambda i: "（" not in i,
                                  extract_str))  # 不可能有括号
        # 两个字分开的名字 进行筛选
        temp_list.extend(extract_str)

    temp_list = list(set(temp_list))
    s = set()
    for temp in temp_list:
        if len(temp.replace(' ', '')) == 2:
            temp = temp.replace(' ', '')
            if get_chinese_name(temp):
                temp = temp
        if '·' in temp:
            temp = temp.strip()
            s.update([temp])
            continue
        extract_zh = re.findall(r"([\u4e00-\u9fa5]+)", temp)
        if extract_zh:
            extract_zh = set(extract_zh)
            s.update(extract_zh)

    result = list(s)
    if result:
        index_len = len(result)
        # 单个元素长度不能超过5个字
        result = list(
            filter(lambda rst: 1 < len(rst) < 5 or "·" in rst, result))
        tmp_result = result[:]
        # 过滤字段可以不用这么多 但不能省略,最后有nlp识别有误差

        filter_word = [
            '了', '的', '在', '亡', '摄', '次', '像', '市', '某', '说', '报', '手', '摄','辆',
            '时', '网', '据', '眼', '哥', '鸭', '街', '省', '手记', '耳中', '透露', '背后','凌晨',
            '荆州', '发现', '简介', '图片', '见习', '知情', '先生', "方式", '周末', '文章', '文字',
            '表示', '刚刚', '整理', '采访', '奔赴', '原标题', '平日', '奉献', '视频', '合肥', '打击',
            '谢谢', '记者', '健康', '周一', '周二', '周三', '周四', '周五', '一线', '踊跃', '北京',
            '万元', '合计', '日摄', '内容', '周六', '周日', '老师', '炎亚', '来源', '解释', '简称',
            '新华社', '版本', '健康', '左二', '古人', '每日', '商城', '跑腿', '生活', '社区', '化名',
            '右1', '资料', '科研', '常年', '关注','平均', '凌晨', '介绍', '文明', '房产', '白天', '高速',
            '校长', '信息', '女士', '先生', '加油', '星期', '恶性', '新区', '厅级', '专业', '放大',
            '点击', '小二', '石家', '纪念'
        ]
        for r in tmp_result:
            for i in filter_word:
                if (i in r or
                    (len(r) <= 3 and not re.match(surname_pattern, r)) or
                    (4 <= len(r) <= 6 and
                     not re.match(compound_pattern, r[:2]))) and ('·'
                                                                  not in r):
                    try:
                        result.remove(r)
                        break
                    except:
                        continue
        result = ' '.join(result).split()
        result = list(
            filter(lambda i: i and len(i) < 11 and '[' not in i,
                   result))  #[英]罗伯特·斯基德尔斯基
        if not result:
            return []
        # logger.info(f"提取到的记者:{result}")
    return result


# 重写 提取记者名
def extract_reporters(text):
    
     #清除所有的标签
    clear_tag_text = clear_all_html2(text)
    raw_text = clear_html_for_reporter(text)
    new_text = raw_text[:50] + "---" + raw_text[-180:]
    # 对有记者字段的文章进行记者提取
    res = get_reporter_list(new_text)
    logger.info(f'有记者字段不调用nlp_ ：{res}')

    if res:
        r = list(filter(lambda word: len(re.findall(word, clear_tag_text[30:-30], re.S)) < 3, res))
        return r
    else:
        all_text = raw_text[:len(raw_text) //
                            7] + "---" + raw_text[-len(raw_text) // 3:]
        res = get_reporter_list(all_text)
        logger.info(f'全文匹配不调用nlp_ ：{res}')
        if res:
            r = list(filter(lambda word: len(re.findall(word, clear_tag_text[30:-30], re.S)) < 3, res))
            return r
        else:
            res = 'Null'
    if res == 'Null':
        logger.info(f'进入没有记者 ： {repr(new_text)}')
        res = get_reporter_excpt_list(new_text)
        logger.info(f'没有记者字段_未调用nlp提取到的人名：{res}')

        res = [get_chinese_name(r) for r in res]  # '晏然' 过滤掉了
        if res:
            logger.info(f'没有记者字段_调用nlp后提取到的记者：{res}')
            r = list(filter(lambda word: len(re.findall(word, clear_tag_text[30:-30], re.S)) < 3, res))
            return r
    return []


# 不经过NLP
def get_reporter_list_1(text_str):
    # print(f'get_reporter_list_1: {text_str}')
    """
    抽到符合条件的记者就直接返回 list，不用经过NLP
    """
    pattern_list = [
        re.compile(
            r'[作记]+.{0,1}[&nbsp;\u3000\xa0\s\u0001\u25a1]*.{0,1}者[(:（：&nbsp;\u3000\xa0\s|丨/\u0001\u25a1]{0,3}([\u4e00-\u9fa5&nbsp;\u3000\xa0\s、\u0001\u25a1]{0,30}?)[编摄报责)）\u0001/]+'
        ),
        re.compile(
            r'[作记]+.{0,1}[&nbsp;\u3000\xa0\s\u0001\u25a1]*.{0,1}者[(:（：&nbsp;\u3000\xa0\s|丨/\u0001\u25a1]{0,3}([\u4e00-\u9fa5&nbsp;\u3000\xa0\s、\u0001\u25a1]{0,20}?)$'
        ),
        re.compile(
            r'[(（]+.{0,10}?[作记]+.{0,1}[&nbsp;\u3000\xa0\s\u0001\u25a1]*.{0,1}者[:：&nbsp;\u3000\xa0\s|丨/\u0001\u25a1]{0,3}([\u4e00-\u9fa5&nbsp;\u3000\xa0\s、\u0001\u25a1]{0,30}?)[编摄报责)）\u0001/]+'
        ),
    ]

    temp_list = []
    for pattern in pattern_list:
        temp_list.extend(re.findall(pattern, text_str))
    temp_list = list(set(temp_list))
    if temp_list:
        reporter_list = []
        for temp_str in temp_list:
            new_str = re.sub(r'\s|\u3000|\xa0|&nbsp;|&nbsp|、|\u0001|\u25a1',
                             ' ', temp_str)
            str_list = new_str.split(' ')
            if len(str_list) <= 3 and len(str_list) >= 2:
                if all(len(i) <= 1 for i in str_list):
                    small_str = ''
                    for i in str_list:
                        if len(i) == 1:
                            small_str += i
                    reporter_list.append(''.join(str_list))
            for x in str_list:
                x = x.strip()
                if '通讯' in x or '编辑' in x or '市场' in x:
                    break
                if len(x) >= 2 and len(x) <= 3:
                    reporter_list.append(x)

        return list(set(reporter_list))

    return []


def extract_reporter_name_strings(text):
    pattern_list = [
        # '[（\(][\s\u3000]*(?!通讯员)(.*?记者.*?)(?=\)|）|通讯|编辑)',
        # '[（\(][\s\u3000]*(?!通讯员)(.*?作者.*?)(?=\)|）|通讯|编辑)',
        # '(?=记者)(.*?)(?=通讯|编辑|）|\))',
        # '(?=作者)(.*?)(?=通讯|编辑|）|\))',
        re.compile(r'[(（]+.{0,10}[记作]+.{0,10}者.{0,40}[）)]+'),
        re.compile(r'(.{0,10}[记作]+.{0,10}者.{0,20})'),
        re.compile(
            r'[记作]+.{0,10}者[(:（：\s\u3000\xa0/|]*([\u4e00-\u9fa5]{2,10})'),
    ]
    # pattern_list = [
    #     re.compile(r'记者[(:（：\s\u3000\xa0/|]*([\u4e00-\u9fa5]{2,10})'),
    #     re.compile(r'作者[(:（：\s\u3000\xa0/|]*([\u4e00-\u9fa5]{2,10})'),
    #     re.compile(
    #         r'记者[(:（：\s\u3000\xa0/|]*([\u4e00-\u9fa5\s\u3000\xa0]+)通讯|编辑|摄'),
    #     re.compile(
    #         r'作者[(:（：\s\u3000\xa0/|]*([\u4e00-\u9fa5\s\u3000\xa0]+)通讯|编辑|摄'),
    #     re.compile(r'记者[(:（：\s\u3000\xa0|]*([\s\xa0\u3000\u4e00-\u9fa5、]+)'),
    #     re.compile(r'作者[(:（：\s\u3000\xa0|]*([\s\xa0\u3000\u4e00-\u9fa5、]+)'),
    # ]
    reporter_name_str_list = []
    for pattern in pattern_list:
        # if reporter_name_str_list:
        #     break
        reporter_name_str_list.extend(re.findall(pattern, text))
    reporter_name_str_list = list(set(reporter_name_str_list))
    # print(f'extract_reporter_name_strings:{reporter_name_str_list}')
    return reporter_name_str_list


def extract_reporter_from_string(reporter_name_str):
    """
    (罗勇 记者 江潇）
    """
    reporter_name_str = re.sub(
        '(\u3000|[\S]*记者|作者|：|\||:|\s|,|/|，|、|\|xa0|&nbsp;|&nbsp)', ' ',
        reporter_name_str)
    reporter_list = reporter_name_str.strip().split()
    # print(f'extract_reporter_from_string:{reporter_list}')
    # Join splited name.
    if len(reporter_list) <= 3 and len(reporter_list) >= 2:
        if all(len(i) == 1 for i in reporter_list):
            reporter_list = [''.join(reporter_list)]
    # Discard reporter names whose length lower than 2.
    reporter_list = [reporter_name for reporter_name in reporter_list \
                     if len(reporter_name) >= 2 and len(reporter_name) <= 4]
    return reporter_list


# def extract_nr_after_reporter(text):
#     pattern = '记者(.{4})'
#     name_str_list = re.findall(pattern, text)
#     res = []
#     for name_str in name_str_list:
#         name = get_namelist_from_hanlp(name_str)
#         if name:
#             res.extend(name)
#
#     if not res:
#         pattern = '作者(.{4})'
#         name_str_list = re.findall(pattern, text)
#         res = []
#         for name_str in name_str_list:
#             name = get_namelist_from_hanlp(name_str)
#             if name:
#                 res.extend(name)
#     return res
# 正则抽取后判断是不是人名。。。。
def get_namelist_from_hanlp(text):
    """
    Extract people name from text.

    :param text [str]: text to extract people name.

    :return: list
    """
    try:
        words_list = pyhanlp.HanLP.segment(text)
    except Exception:
        words_list = []

    if not words_list:
        return []

    people_name_list = []
    for word in words_list:
        if str(word.nature) in ['nr', 'nrf', 'nrj']:
            people_name_list.append(str(word.word))
    return people_name_list


# 提取通讯员main
def extract_correspondents(text):
    raw_text = clear_all_html(text)
    if len(raw_text) > 150:
        new_text = raw_text[:100] + raw_text[-50:]
    else:
        new_text = raw_text

    # 保存最终返回的通讯员列表
    res = []

    # 不经过 NLP
    res = get_correspondent_list_1(clear_html_for_reporter(text))
    # 阿里云人名判断
    res = [get_chinese_name(str(r)) for r in res]
    if res:
        return res

    # 在前100行和后50行抽取通讯员
    # print(new_text)
    name_str_list = extract_correspondent_name_strings(new_text)
    for name_str in name_str_list:
        name_list = extract_correspondent_from_string(name_str)
        res.extend(name_list)
    res = list(set(res))

    # 正则抽取到通讯员后，用 NLP 判断是不是人名
    if res:
        temp_list = []
        for name_str in res:
            temp_list.extend(get_namelist_from_hanlp(name_str))
        res = list(set(temp_list))

    if not res:
        # 正则抽取不到通讯员，就全文抽取，重复上面步骤
        name_str_list = extract_correspondent_name_strings(raw_text)
        for name_str in name_str_list:
            name_list = extract_correspondent_from_string(name_str)
            res.extend(name_list)
        res = list(set(res))

        if res:
            temp_list = []
            for name_str in res:
                temp_list.extend(get_namelist_from_hanlp(name_str))
            res = list(set(temp_list))

    # 阿里云人名判断
    res = [get_chinese_name(str(r)) for r in res]
    if res:
        return res


def extract_correspondent_name_strings(text):
    pattern_list = [
        # '[（\(][\s\u3000]*(?!通讯员)(.*?记者.*?)(?=\)|）|通讯|编辑)',
        # '[（\(][\s\u3000]*(?!通讯员)(.*?作者.*?)(?=\)|）|通讯|编辑)',
        # '(?=记者)(.*?)(?=通讯|编辑|）|\))',
        # '(?=作者)(.*?)(?=通讯|编辑|）|\))',
        re.compile(r'[(（]+.{0,10}通讯员.{0,40}[）)]+'),
        re.compile(r'(.{0,10}通讯员.{0,20})'),
        re.compile(r'通讯员[(:（：\s\u3000\xa0/|]*([\u4e00-\u9fa5]{2,10})'),
    ]
    # pattern_list = [
    #     re.compile(r'记者[(:（：\s\u3000\xa0/|]*([\u4e00-\u9fa5]{2,10})'),
    #     re.compile(r'作者[(:（：\s\u3000\xa0/|]*([\u4e00-\u9fa5]{2,10})'),
    #     re.compile(
    #         r'记者[(:（：\s\u3000\xa0/|]*([\u4e00-\u9fa5\s\u3000\xa0]+)通讯|编辑|摄'),
    #     re.compile(
    #         r'作者[(:（：\s\u3000\xa0/|]*([\u4e00-\u9fa5\s\u3000\xa0]+)通讯|编辑|摄'),
    #     re.compile(r'记者[(:（：\s\u3000\xa0|]*([\s\xa0\u3000\u4e00-\u9fa5、]+)'),
    #     re.compile(r'作者[(:（：\s\u3000\xa0|]*([\s\xa0\u3000\u4e00-\u9fa5、]+)'),
    # ]
    correspondent_name_str_list = []
    for pattern in pattern_list:
        # if correspondent_name_str_list:
        #     break
        correspondent_name_str_list.extend(re.findall(pattern, text))
    correspondent_name_str_list = list(set(correspondent_name_str_list))
    # print(f'extract_correspondent_name_strings:{correspondent_name_str_list}')
    return correspondent_name_str_list


def extract_correspondent_from_string(correspondent_name_str):
    """
    (通讯员 江潇）
    """
    correspondent_name_str = re.sub(
        '(\u3000|[\S]*通讯员|：|\||:|\s|,|/|，|、|\|xa0|&nbsp;|&nbsp)', ' ',
        correspondent_name_str)
    correspondent_list = correspondent_name_str.strip().split()
    # print(f'extract_correspondent_from_string:{correspondent_list}')
    # Join splited name.
    if len(correspondent_list) <= 3 and len(correspondent_list) >= 2:
        if all(len(i) == 1 for i in correspondent_list):
            correspondent_list = [''.join(correspondent_list)]
    # Discard correspondent names whose length lower than 2.
    correspondent_list = [correspondent_name for correspondent_name in correspondent_list \
                          if len(correspondent_name) >= 2 and len(correspondent_name) <= 4]
    return correspondent_list


def get_correspondent_list_1(text_str):
    # print(f'get_correspondent_list_1: {text_str}')
    """
    抽到符合条件的通讯员就直接返回 list，不用经过NLP
    """
    pattern_list = [
        re.compile(
            r'通讯员[(:（：&nbsp;\u3000\xa0\s|丨/\u0001\u25a1]{0,3}([\u4e00-\u9fa5&nbsp;\u3000\xa0\s、\u0001\u25a1]{0,30}?)[编摄报责)）\u0001/]+'
        ),
        re.compile(
            r'通讯员[(:（：&nbsp;\u3000\xa0\s|丨/\u0001\u25a1]{0,3}([\u4e00-\u9fa5&nbsp;\u3000\xa0\s、\u0001\u25a1]{0,20}?)$'
        ),
        re.compile(
            r'[(（]+.{0,10}?通讯员[:：&nbsp;\u3000\xa0\s|丨/\u0001\u25a1]{0,3}([\u4e00-\u9fa5&nbsp;\u3000\xa0\s、\u0001\u25a1]{0,30}?)[编摄报责)）\u0001/]+'
        ),
    ]

    temp_list = []
    for pattern in pattern_list:
        temp_list.extend(re.findall(pattern, text_str))
    temp_list = list(set(temp_list))
    if temp_list:
        correspondent_list = []
        for temp_str in temp_list:
            new_str = re.sub(r'\s|\u3000|\xa0|&nbsp;|&nbsp|、|\u0001|\u25a1',
                             ' ', temp_str)
            str_list = new_str.split(' ')
            if len(str_list) <= 3 and len(str_list) >= 2:
                if all(len(i) <= 1 for i in str_list):
                    small_str = ''
                    for i in str_list:
                        if len(i) == 1:
                            small_str += i
                    correspondent_list.append(''.join(str_list))
            for x in str_list:
                x = x.strip()
                if '记者' in x or '编辑' in x or '市场' in x or '作者' in x:
                    break
                if len(x) >= 2 and len(x) <= 3:
                    correspondent_list.append(x)

        return list(set(correspondent_list))

    return []


def clear_all_html(html):
    #"""
    #Python中过滤HTML标签的函数
    #>>> str_text=strip_tags("<font color=red>hello</font>")
    #>>> print str_text
    #hello
    #"""
    html = html.strip()
    html = html.strip("\n")

    result = []
    parser = HTMLParser()
    parser.handle_data = result.append
    parser.feed(html)
    parser.close()
    result = ''.join(result)
    result = result.replace("\n", "")
    return result


def clear_all_html2(text):
    new_text = re.sub(r'<[^>]+>','\u0001', text)
    return new_text.strip()


def clear_html_for_reporter(text):
    #别加 re.S
    new_text = re.sub(
        r'<!--.*?-->|<script.*?/script>|<style.*?/style>|<.*?>|&nbsp;',
        '\u0001', text)
    new_text = re.sub(r'\u0001{1,}', '\u0001', new_text)
    new_text = re.sub(r'\u0001 \u0001', '', new_text)
    return new_text.strip()


def map_internal_category(tencent_first_level_categroy, second_level_category):
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


def test_reporters():
    # text_list = [
    #     '美国《华盛顿邮报》《纽约时报》和《华尔街日报》的出版人24日联合签署给中国政府的公开信，要求撤回取消三家媒体部分美籍记者在华记者证的决定。对此，中国外交部发言人耿爽24日再次表示，如果哪家美国媒体，包反对的是借所谓新闻自由炮制假新闻，反对的是违反新闻职业道德的行为。来源：环球网编辑：莫愁审核：周佳佳',
    #     '926 1583734021319982 广州日报讯\u3000（全媒体记者\u3000 黎慧莹 通讯员 穗妇宣）',
    #     '（本报记者  刘岩松  通讯员  曾  强）',
    #     '本报讯（罗勇 记者 江潇）3月',
    #     '（记者/简文湘 通讯员/罗江莉）',
    #     ' 社福州3月7日电 （记者康淼 邰晓安 王成）记者从福建省泉州市委宣传部',
    #     '（记者肖亚卓）',
    #     '（记者王玉洁 通讯员李红波）',
    #     '（记者 张  娅）',
    #     '（记者 张 胜 男）',
    #     '（本报记者顾仲阳、张帆、徐元锋、庞革平、王明峰、王汉超、蒋云龙、朱佩娴、程焕）',
    #     '（通讯员 建萱 融媒体记者 卫凌云）',
    #     '（湖北日报全媒记者 张鸿 通讯员 谢丹 齐艳 摄）',
    #     '辽沈晚报首席记者 赵天乙',
    #     '◎文/徐报融媒记者 王正喜 图/徐报融媒记者 陈艳',
    #     '羊城晚报讯 记者诸葛万报道：“出棋制胜',
    #     '<div class="rich_media_content " id="js_content"> <section><section powered-by="xiumi.us"><section><section powered-by="xiumi.us"><section><img data-ratio="0.140625" data-type="gif" data-w="320" class="__bg_gif" src="https://images.mediarank.cn/FknIFU6Fqiz3GcBjN2HhqXJ0JfTS"/></section></section></section></section><section powered-by="xiumi.us"><section><section powered-by="xiumi.us"><section><p>点击上方“<strong>廊坊日报</strong>” 关注我们</p></section></section></section></section><section powered-by="xiumi.us"><section><section powered-by="xiumi.us"><section><img data-ratio="0.140625" data-type="gif" data-w="320" class="__bg_gif" src="https://images.mediarank.cn/FktoVhxBZCwOZ1zpf1Tb6eVD4-i9"/><span/></section></section></section></section></section><section><section powered-by="xiumi.us"><section><section><section powered-by="xiumi.us"><section><section powered-by="xiumi.us"><section><section><section powered-by="xiumi.us"><section><section><p><span><strong><span>省委办公厅省政府办公厅联合印发《通知》</span></strong></span></p><p><span><strong><span>全面恢复正常生产生活秩序和医疗秩序</span></strong></span></p><p><span><strong><span>统筹推进疫情防控和经济社会发展工作</span></strong></span></p><p><br/></p></section></section></section></section></section></section></section><p><span>河北日报讯（记者四建磊）当前，我省疫情防控形势持续向好，全省各县（市、区）均为低风险地区。为深入贯彻习近平总书记重要讲话精神和中央政治局常务委员会会议精神，认真落实中央应对新冠肺炎疫情工作领导小组会议要求，日前，省委办公厅、省政府办公厅联合印发《关于全面恢复正常生产生活秩序和医疗秩序统筹推进疫情防控和经济社会发展的通知》（以下简称《通知》）。</span></p><p><br/></p><p><span>《通知》提出了六个方面政策措施和要求。</span></p><p><br/></p><p><strong><span>一是始终坚持政治站位，</span></strong><strong><span>坚决贯彻习近平总书记重要讲话精神和党中央决策部署。</span></strong><span>要准确把握当前疫情防控和经济形势的阶段性变化，因时因势调整工作着力点和应对举措，毫不放松抓紧抓实抓细各项工作，坚决当好首都政治“护城河”，确保实现决胜全面建成小康社会、决战脱贫攻坚目标任务和“十三五”规划圆满收官。</span></p><p><br/></p><p><strong><span>二是全面推进复工复产，</span></strong><strong><span>加快建立同疫情防控相适应的经济社会运行秩序。</span></strong><span>要简化复工复产程序，全面实行告知承诺制，对低风险地区之间的人员和货物流动，要互认必要的健康证明。要尽快推动复产企业产能恢复，全面落实减税降费、财政贴息、金融支持等政策，有效解决企业资金困难。要大力推动疫情影响严重行业企业复工复产，开展“暖企助企”行动，出台餐饮、住宿、旅游、物流等行业恢复运营平稳发展的政策措施。要强化复工复产服务保障，以开展“三创四建”活动为抓手，健全完善省市县三级领导包联和特派员、联络员制度，“一企一策”解决企业用工、资金、原材料供应等困难。</span></p><p><br/></p><p><strong><span>三是坚持科学精准防控，</span></strong><strong><span>坚决打赢疫情防控的人民战争、总体战、阻击战。</span></strong><span>要强化境外输入疫情防控，完善数据共享、信息通报和入境人员核查机制，全面加强入境航班、班列、船只的监测和管控，严格落实入境人员转运、隔离、留观、治疗等措施。要严防严控“三道防线”，大力强化与京津及周边省区联防联控，牢牢守住入京通道防线。要加强抗疫物资储备保障，抓好医用防护服、隔离衣、口罩生产储备，保证复工复产和复学复课需求，进一步加大对湖北武汉和神农架林区支援力度。要做深做实基础性排查，全面动态排查社区和农村，进一步强化重点场所、机关事业单位、复工复产企业和商场、超市等人员密集场所、公共场所排查防控工作。要加强出院患者愈后管理，有效推动正常医疗秩序恢复。要保护关心爱护医务人员，落实落细各项服务保障和激励措施。</span></p><p><br/></p><p><strong><span>四是深化风险排查整治，</span></strong><strong><span>扎实做好安全生产、森林草原防火等工作。</span></strong><span>要严格落实市县属地责任、部门行业监管责任、企业主体责任，深入推进重点行业领域安全生产专项整治。要全力抓好森林草原防火，突出环京津、冬奥赛区、雄安新区、塞罕坝等重点区域和清明、“五一”等重点时段，组织开展野外火源专项治理行动。要大规模开展国土绿化，加快雄安绿博园、森林城市创建和首都“两区”建设，全面改善生态环境质量。</span></p><p><br/></p><p><strong><span>五是加强经济运行调度，</span></strong><strong><span>努力完成全年经济社会发展目标任务。</span></strong><span>要加强监测分析调度，强化对重点地区、重点行业、重点企业的运行监测，力促主要指标企稳回升，确保一季度开好局起好步。要抓好投资项目建设，对重点项目审批开辟“绿色通道”，保障项目建设投资需求和土地供应。要加快服务消费扩容提质，扩大对外经贸合作，有效防范化解风险，优化经济秩序和投资环境。</span></p><p><br/></p><p><strong><span>六是压实各级各部门工作责任，</span></strong><span><strong><span>确保各项措施落实落细落地。</span></strong></span><span>要严格落实各级党委、政府责任，发挥领导包联作用和各部门职能作用，强化督导检查和政治监督，确保党中央决策部署和省委、省政府要求不折不扣落到实处、见到实效。</span></p></section></section></section></section></section><p><img class="rich_pages" data-ratio="1.4625228519195612" data-s="300,640" src="https://images.mediarank.cn/FjEWlbvlNS5lbFDdStBXcNWvjIvT" data-type="jpeg" data-w="547"/><br/></p><p><strong/></p><p><span><strong/></span></p><p><span><strong>来源：河北日报官方微信</strong></span></p><p><strong>编辑：葛雪梅</strong></p><p><span><strong>审核：</strong><strong>王文珩 刘杰</strong></span></p><p><img class="rich_pages" data-ratio="0.47415730337078654" data-s="300,640" data-type="jpeg" data-w="445" src="https://images.mediarank.cn/FlAAmpot8-0py0n1pcTsA5CP966g"/><br/></p><p><img class="rich_pages" data-ratio="0.1328125" data-s="300,640" data-type="jpeg" data-w="640" src="https://images.mediarank.cn/FpW8zD4pBcoDTv3RyItuXQ5UmYQO"/></p> </div>',
    #     '<div class="rich_media_content " id="js_content"> <p><span><span>点击上方</span><span>“华商报”</span><span>可快速关注哦！</span></span></p><section><span>　　3月23日，按照陕西省政府、国家文物局新冠肺炎疫情防控和复工复产的有关指导意见，陕西省文物局确定陕西历史博物馆、秦始皇帝陵博物院、西安碑林博物馆、汉景帝阳陵博物院四家直属博物馆拟于3月25日同时对外恢复开放。</span><br/><br/><img class="rich_pages" data-ratio="0.5625" data-s="300,640" data-type="jpeg" data-w="1280" src="https://images.mediarank.cn/FuCltIKCho4nJ4FHab3MGq9GeuGs"/><br/></section><article data-author="Wxeditor"><section><section><p><span>　　</span><span>四家省直属博物馆恢复开放后采取线上线下预约参观，</span><span><strong><span>暂时不接待团队参观和不提供人工讲解</span></strong></span><span>。<br/></span></p><p><span>■</span><span>陕西历史博物馆每日参观限额为2000人次，何家村专题展和唐墓壁画珍品馆暂不开放；<br/></span></p><p><span><span>■</span>秦始皇帝陵博物院每日参观限额为8000人次，执行原来的票价；<br/></span></p><p><span><span>■</span>西安碑林博物馆每日参观限额为1000人次，免费开放至5月底；<br/></span></p><p><span><span>■</span>汉景帝阳陵博物院每日参观限额为2000人次,免费开放3个月，外藏坑遗址保护展示厅暂不开放。<br/></span></p><section><span>具体线上线下预约参观办法由各馆（院）另行公告。</span></section></section></section></article><p><br/><span/></p><section><span>　　陕西省文物局组织制定了博物馆恢复开放期间“疫情防控工作方案”和“开放应急预案”，确保博物馆在开放前应急措施到位、人员健康上岗、物资保障充足、观众安全参观；同时按照“事前预警，事中处理，事后追溯”全流程管控目标，组织研发了国内首套集物联网、大数据和人工智能等技术于一体的博物馆公共卫生防疫监测数据采集系统，可快速甄别出观众中潜在传染性疫情的危险因素；通过控制最大参观人数和瞬时人流、严格落实疫情防控各项措施，切实做好馆区日常防控管理和人员日常防护管护，实现有效防控疫情和有序恢复开放双目标。<br/>　　<br/>　　此前，陕西省文物局还制定下发了“关于新冠肺炎疫情防控期间全省博物馆、纪念馆有序恢复开放的指导意见”，指导各设区市按照“精准施策、分区分级、属地管理”原则实行“一馆一策、一馆一案”制度，建立博物馆恢复开放工作机制，稳妥推进全省博物馆、纪念馆有序恢复开放。各设区市按照相关要求积极制定博物馆恢复开放管理预案和具体措施，</span><span><strong><span>截至目前全省共有38家博物馆、纪念馆和25家文物类景区已陆续恢复对外开放。</span></strong></span><span><br/>　　<br/></span><span>华商报记者 马虎振</span><br/></section> </div>',
    #     '<div class="rich_media_content " id="js_content"> <p><img class="rich_pages __bg_gif" data-ratio="0.0765625" data-type="gif" data-w="640" src="https://images.mediarank.cn/FoGmblFJ5UDNFBzE95Bu-EzSA4GC"/></p><p><img class="rich_pages" data-ratio="0.31015625" data-s="300,640" src="https://images.mediarank.cn/FsjicrtdFWd0iL7lQ6rHkeOT4DQL" data-type="jpeg" data-w="1280"/></p><p><br/></p><section>临夏州综合分析研判疫情对脱贫攻坚产生的影响，研究部署挂牌督战，主动加压靠实责任，确保高质量完成3.25万人脱贫、66个贫困村退出、临夏县和东乡县2个贫困县摘帽的任务，决战决胜脱贫攻坚。<br/></section><section><br/></section><section>印发《临夏州脱贫攻坚挂牌督战实施方案》，对贫困发生率高于10%以上的38个村由地级领导挂牌督战，对贫困发生率5%—10%的38个村由地级领导包抓、县级领导挂牌督战，未脱贫人口、边缘户和监测户由县级领导主抓、帮扶干部盯死看牢，逐户逐人逐项落细抓实。力争5月底彻底解决“两不愁三保障”短板弱项，6月底全部清零见底。</section><section><br/></section><section>狠抓劳动力返岗复工，制定出台扶持劳动力就业的政策措施，加强与劳务中介机构和劳务输入地的协调联系，通过“专车护送、专派医务人员护理、专派管理干部全程服务”等方式，积极实施农民工返岗复工“专项行动”，组织务工人员到福建、江苏、江西等地就业。积极开发3000个临时公益性岗位安置未就业人员，大力推动扶贫车间复产复工，实现就近就业。</section><section><br/></section><section>全力推动春季农业生产，实施种植业结构调整“60万亩工程”，推广“粮改菜、粮改药、粮改油、粮改果、粮改饲”，因地制宜推广高原夏菜、食用菌、中药材、百合、藜麦、经济林果等高产高效作物；加强农资调运储备，组织全州887家农资经营门店恢复营业，储备农作物良种、化肥、有机肥、农膜、农药，满足春耕生产需要；督促各县选择实力强、网点全、服务好的保险机构提供农业保险服务，做到应保尽保、愿保必保，提高抵御风险能力。（<strong>记者</strong> 马尚龙）</section><section><br/></section><section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section></section><section><br/></section><section><strong><span>责编：</span></strong><span>范海东 <strong>编辑：</strong>山桦 <strong>校对：</strong>张皓静</span><br/></section><p><br/></p><p><img class="rich_pages __bg_gif" data-ratio="0.29984301412872844" data-type="gif" data-w="637" src="https://images.mediarank.cn/Fiz1wLtrZVy6lbggOsVR49lWx7es"/></p><p><img class="rich_pages" data-ratio="0.5125" data-s="300,640" data-type="jpeg" data-w="1280" src="https://images.mediarank.cn/Frrmn-JjFVFkt118SFmawAbPGDhe"/></p> </div>',
    #     '<div class="rich_media_content " id="js_content"> <section><span><strong><span>千里驰援</span></strong></span></section><section><span><strong><span>今朝凯旋</span></strong></span></section><p><br/></p><section>根据国家统一部署<br/></section><p><span>江西369名援随人员</span></p><p><span>今日踏上归程</span></p><p><span>其中包括352名医护人员</span></p><p><br/></p><p><iframe class="video_iframe rich_pages" data-vidtype="2" data-mpvid="wxv_1263993392376217600" data-cover="http%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_jpg%2FiatibqvCsmT63qeWGHnPCGdBH9KWPPib4t9wiaoSLcmclXPEfB9aia68Y6vWuDR31uR1ibW3Tstj4Cqzg4kKCqTbDUaA%2F0%3Fwx_fmt%3Djpeg" allowfullscreen="" frameborder="0" data-ratio="1.7391304347826086" data-w="640" src="https://images.mediarank.cn/FnDlMxA2pKIUEId1uKTY_Q_SfWKf"/></p><section><br/></section><p><img class="rich_pages" data-ratio="0.5625" data-s="300,640" src="https://images.mediarank.cn/FlOzarJZhMU8LQsi23T_MPY1Lkva" data-type="jpeg" data-w="1280"/></p><section><img class="rich_pages" data-ratio="0.5625" data-s="300,640" src="https://images.mediarank.cn/FkKRJOh-RfTnZhI6x6agezXAghTF" data-type="jpeg" data-w="1280"/></section><section><br/></section><section data-tools="135编辑器" data-id="47131" data-color="#ac1d10"><section><section><section><br/></section><section><br/></section></section><section><section><span><span>我省援随人员共407名，其中医护人员共389名，分别于2月7日、11日和17日抵达随州。</span><strong><span>赣州在随州共有队员179人，其中医技人员72人，护士107人。</span></strong></span></section><section><span><br/></span></section><section><span><strong/><span>截至目前，江西援随医疗队累计接管12个病区，管理患者607例，其中重症、危重症75例，累计治愈出院575例。</span><span>为协助随州市做好疫情防控和患者救治工作，</span><span>江西援随医疗队仍有38名医护人员和防疫专家继续留守随州。</span></span></section></section><section><section><br/></section><section><br/></section></section></section></section><section><br/></section><p><iframe class="video_iframe rich_pages" data-vidtype="2" data-mpvid="wxv_1264003499625447425" data-cover="http%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_jpg%2FiatibqvCsmT63qeWGHnPCGdBH9KWPPib4t9ibichMhZjT7apyicv1tEzAjVsUSeePiaoKEqFndOvIPR7fBymFLp7PuKvg%2F0%3Fwx_fmt%3Djpeg" allowfullscreen="" frameborder="0" data-ratio="0.5666666666666667" data-w="544" src="https://images.mediarank.cn/FnDlMxA2pKIUEId1uKTY_Q_SfWKf"/></p><section><br/></section><p><img class="rich_pages" data-backh="321" data-backw="560" data-ratio="0.5732142857142857" src="https://images.mediarank.cn/Fs6Up6BWUZh4GLWnZm1LDqsjUjc4" data-type="gif" data-w="560"/></p><p><img class="rich_pages" data-ratio="0.5625" data-s="300,640" src="https://images.mediarank.cn/FhWAov7Dt1WLW_qmw0hyHTNPqZoG" data-type="jpeg" data-w="1280"/></p><p><br/></p><section><span>樱花烂漫</span></section><section><span>送别亲爱的战友凯旋</span></section><section><span>再见，最可爱的人</span></section><section><span>谢谢你们义无反顾、逆行随州</span></section><section><span>谢谢你们为我们拼过命</span></section><section><br/></section><p><img class="rich_pages" data-ratio="0.5732142857142857" src="https://images.mediarank.cn/Fs7W3BzhvEbm8TWrWhUv_87nlky8" data-type="gif" data-w="560"/></p><p><img class="rich_pages" data-ratio="0.5660714285714286" src="https://images.mediarank.cn/FvVqZSeGoP5N8eeOFWmyH2me5pok" data-type="gif" data-w="560"/></p><p><br/></p><section><span>再见</span></section><section><span>亲爱的随州朋友</span></section><section><br/></section><p><iframe class="video_iframe rich_pages" data-vidtype="2" data-mpvid="wxv_1264000227615342593" data-cover="http%3A%2F%2Fmmbiz.qpic.cn%2Fmmbiz_jpg%2FiatibqvCsmT63qeWGHnPCGdBH9KWPPib4t9jSZxpiaBpyh296IduBe2rGkicAxmBzicSMokK1ZZL2iaAcPkyIxZH2IF8Q%2F0%3Fwx_fmt%3Djpeg" allowfullscreen="" frameborder="0" data-ratio="1.7647058823529411" data-w="960" src="https://images.mediarank.cn/FnDlMxA2pKIUEId1uKTY_Q_SfWKf"/></p><p><br/></p><section><span>46个日日夜夜<br/></span></section><section><span>我们心相连，情相牵</span></section><section><span>待山花烂漫，我们再次相约</span></section><section><span>听一曲离骚，赏赤壁烈焰</span></section><section><br/></section><section><img class="rich_pages" data-ratio="0.5" data-s="300,640" src="https://images.mediarank.cn/FgMiaTK256HevmEos15ygad0xjL1" data-type="jpeg" data-w="1280"/></section><p><img class="rich_pages" data-ratio="0.66640625" data-s="300,640" src="https://images.mediarank.cn/FjKpN_QK5rQI1_zdoRlt0Xyi6Sg0" data-type="jpeg" data-w="1280"/></p><p><img class="rich_pages" data-ratio="0.66640625" data-s="300,640" src="https://images.mediarank.cn/FsyY9BxQcALziRNhSJM67aHv5C3d" data-type="jpeg" data-w="1280"/></p><p><br/></p><section data-tools="135编辑器" data-id="86318" data-color="#374aae"><section><section><section><span><strong><span data-brushtype="text">江西支援随州大事记</span></strong></span></section></section></section></section><section><br/></section><p><span><strong><span>◈</span></strong>2月7日凌晨，江西省第一批援随医疗队135人抵达随州。</span></p><p><br/></p><p><span><strong><span>◈</span></strong>2月11日晚，江西援随前方指挥部和江西省第二批援随医疗队143人抵达随州。</span></p><p><br/></p><p><span><strong><span>◈</span></strong>2月14日，“江西省对口支援湖北省随州市新冠肺炎防治工作前方指挥部临时党委”成立。</span></p><p><br/></p><p><span><strong><span>◈</span></strong>2月17日晚，江西省第三批对口支援随州医疗队126人抵达随州。</span></p><p><br/></p><p><span><strong><span>◈</span></strong>2月14日，江西支援随州医疗和生活保障物资物流专线正式开通，江西省支援随州的4辆负压式救护车正式捐赠交付，成为江西省第一批抵达随州的捐赠医疗器械。</span></p><p><br/></p><p><span><strong><span>◈</span></strong>2月14日，江西支援随州医疗和生活保障物资物流专线正式开通。当日下午，江西省支援我市的4辆负压式救护车正式捐赠交付，成为江西省第一批抵达我市的捐赠医疗器械。2月15日凌晨，援随第一批医疗保障物资抵达随州。</span></p><p><br/><span><strong><span>◈</span></strong>2 月19 日晚，江西省支援我市防疫物资抵随，总价值1000余万元。</span></p><p><br/></p><p><span><strong><span>◈</span></strong>2月16日，中共中央政治局委员、国务院副总理孙春兰率中央指导组来到随州，实地指导社区疫情防控，看望并慰问了江西援随医疗队。</span></p><p><br/></p><p><span><strong><span>◈</span></strong>2月19日，江西省委书记刘奇、省长易炼红，与湖北省随州市委书记陈瑞峰、市长克克视频连线，会商援随工作。刘奇在视频连线时说：“我们一定把随州的事当江西的事来办，与随州人民风雨同舟、并肩作战，不获全胜、决不收兵。”陈瑞峰向江西对随州的倾力支持表示感谢。双方一致表示，共同做好对口支援各项工作，坚决打赢疫情防控人民战争、总体战、阻击战。</span></p><p><br/></p><p><span><strong><span>◈</span></strong>2月20日，江西援随医疗队接管的曾都医院感染八病区一名43岁的女性患者治愈出院，成为江西援随医疗队全程接管病区以来第一位正式出院的新冠肺炎患者。</span></p><p><br/></p><p><span><strong><span>◈</span></strong>2月25日，江西省支援随州的9套远程医疗系统，正式上线启用，进行了重症患者远程会诊。3月6日，江西省援随医疗队组织完成与江西省人民医院、南昌大学第一、二附属医院、赣南医学院附属医院的跨省远程多学科会诊17人次，取得良好的临床效果。</span></p><p><br/></p><p><span><strong><span>◈</span></strong>2月25日，江西援随医疗队8名同志第一批火线入党。</span></p><p><br/></p><p><span><strong><span>◈</span></strong>3月5日，江西省援随医疗队队员袁小亮、邓丽花荣获“全国卫生健康系统新冠肺炎疫情防控工作先进个人”称号。以江西省援随防疫组流行病学和核酸检测专家为主体的疾控系统驻随州防控小分队，荣获“全国卫生健康系统新冠肺炎防控工作先进集体”。</span></p><p><br/></p><p><span><strong><span>◈</span></strong>3月13日，江西援随医疗队在曾都医院种下友谊树；3月20日，在广水印台山生态公园种下友谊树，“赣”恩有你、“鄂”记心上，铭记这段特殊的抗疫历史，见证赣随人民“风雨同舟，共抗疫情”的深厚友谊。</span></p><p><br/></p><p><span><strong><span>◈</span></strong>3月15日下午，随县人民医院最后一名新冠肺炎确诊患者王某治愈出院，江西省对口支援随州医疗队累计接管的607例患者中，普通患者实现全面“清零”。</span></p><p><br/></p><p><span><strong><span>◈</span></strong>3月16日，赣南医学院与广水市人民政府签订战略合作协议。3月22日，赣南医学院与随县人民政府签订战略合作协议，江西省人民医院与随州市中心医院签订战略合作协议，赣州市人民医院与曾都医院签订战略合作协议，赣南医学院第一附属医院与广水市第一人民医院签订战略合作协议，为随州打造一支带不走的医疗队。</span></p><p><br/></p><p><span><strong><span>◈</span></strong>3月23日，按照中央指导组统一部署，江西援随医疗队将留下防疫组13名同志和医疗小分队25名同志、其他369名同志将启程返回江西。</span></p><p><br/></p><p><img class="rich_pages" data-ratio="0.6703125" data-s="300,640" src="https://images.mediarank.cn/FuCtOYPAiksZy2gsjaBMSpMvY9Hn" data-type="jpeg" data-w="1280" data-backw="578" data-backh="387"/></p><p><br/></p><section>谢谢你们</section><section>叫不上你们的名字</section><section>只知道你们是援随医疗队的英雄</section><section>看不到你们的面孔</section><section>只看到你们露在口罩外的双眼</section><p><br/></p><section><span><span><strong>白衣战士</strong></span></span></section><section><span><strong><span>你们辛苦了</span></strong></span></section><p><br/></p><hr/><p><span>来源：赣南日报</span></p><p><span>作者：赣南日报特派随州记者陈地长<br/></span></p><section data-role="outer" label="Powered by 135editor.com"><section data-role="paragraph"><section data-role="paragraph"><section data-role="paragraph"><section data-role="paragraph"><section data-role="paragraph"><section data-role="paragraph"><section data-role="paragraph"><p><span>编辑：黄松林 校对：刘敏</span></p><section><section data-role="paragraph"><section data-role="paragraph"><section data-role="paragraph"><section data-role="paragraph"><p><span>值班主任：明心武  编审：陈昱鑫</span></p></section></section></section></section></section></section></section></section></section></section></section></section></section><p><img width="677" data-ratio="0.49" data-type="jpeg" data-w="700" src="https://images.mediarank.cn/FuIupnjLGM3Ms4ksKTUaKzDnKJwz"/></p> </div>',
    #     '<div class="rich_media_content " id="js_content"> <p><img class="rich_pages __bg_gif" data-ratio="0.0765625" data-type="gif" data-w="640" src="https://images.mediarank.cn/FoGmblFJ5UDNFBzE95Bu-EzSA4GC"/><br/></p><p><img class="rich_pages" data-ratio="0.31" data-s="300,640" src="https://images.mediarank.cn/FnEqpA4NiWVokgDYwNllKA7FKICc" data-type="jpeg" data-w="700"/></p><p><br/></p><p><span><strong>母亲河畔春色好</strong></span><strong><br/>——临夏县河西乡见闻</strong></p><p><br/></p><section>3月20日，记者来到临夏县河西乡，春天的气息渐浓，田野里散发着嫩草、枝芽和泥土淡淡的香味；田地和项目建设现场，处处都是人们忙碌的身影……勾勒出最美的春色！</section><section><br/></section><section><img class="rich_pages" data-ratio="0.66171875" data-s="300,640" src="https://images.mediarank.cn/FlQV3DOxLLLV1oWbaDW2enbwZ1Vo" data-type="jpeg" data-w="1280"/></section><section><br/></section><section data-support="96编辑器" data-style-id="25301"><section><p><img data-ratio="0.8780487804878049" src="https://images.mediarank.cn/FkvMEcWpXwj6wjL6zN7DmM_0GxNj" data-type="gif" data-w="41"/></p><section><section><p><strong><span>十里鲜花喷薄欲出</span></strong></p></section></section><section><p><img data-ratio="0.8780487804878049" src="https://images.mediarank.cn/FmBWdkQuFCb0xgmkPEh9CKTpxzf4" data-type="gif" data-w="41"/></p></section></section></section><section><br/></section><section><span>河西乡东、南、北三面被大夏河和刘家峡水库所环绕，西面是陡峭的北塬面山。</span><span>夹在水和山之间的河西乡，南北长有10公里、东西宽3公里，总面积只有13平方公里。</span><span>特殊的地理位置，造就了特殊的生态环境，自古就有“瓜果之乡”美誉的河西乡，盛产杏子、瓜瓜子、巴梨、阳面红、苹果、伏梨、早酥梨、大樱桃、油桃等十多种优质水果。</span><br/></section><section><span><br/></span></section><p><img class="rich_pages" data-ratio="0.6703125" data-s="300,640" src="https://images.mediarank.cn/FtMFfuACSjH92xSBP37vIWaIIVpB" data-type="jpeg" data-w="1280"/></p><section><br/></section><section>“打造田园综合体，发展乡村旅游业，这里遍地的经济林果业发展基础是先决优势条件，三季赏花、四季有果在河西乡正在大做文章，这个春天我们借势再发力……”河西乡负责人告诉记者。</section><section><br/></section><p><img class="rich_pages" data-ratio="0.66171875" data-s="300,640" src="https://images.mediarank.cn/Fnp86iZouUDx_KSwohjyAbn21to_" data-type="jpeg" data-w="1280"/></p><section><br/></section><section>据介绍，河西乡从南向北，这里原有的大夏河河谷地300亩苹果林，虽然树龄不长，但春天鲜花盛开，参差分明格外美丽；紧挨着的是200多亩的杏子林，树龄大都40多年，由于杏子常年被青海省西宁客商年初付款订购，杏农们精心管理每一株树，春天鲜花繁盛，看杏花确实是一种享受；梨树分布很广，田野里、村庄房前屋后到处都是，每逢春天，河西到处都有梨花盛开，村庄掩映在一片花海里……</section><section><br/></section><p><img class="rich_pages" data-ratio="0.66171875" data-s="300,640" src="https://images.mediarank.cn/Fni83S-H4mRhBCV9nAUmELnAeI1n" data-type="jpeg" data-w="1280"/></p><section><br/></section><section>记者沿着田间的条条水泥路行走，每一块田，不时看到农民为果树施肥，清理田地，一排排修建整齐的果树下是整洁的土地、绵绵的土壤，田间地头管理的有条不紊。在塔张村，新栽植300亩油桃树，从库区水边一直延生到山脚下。村民常全平正在油桃施肥，他不好意思地说：“别人都已经给树上了肥，我要抓紧……”</section><section><br/></section><section>为了把花的文章做好，河西乡还调整产业结构，压缩小麦、玉米种植面积，今春又种了300多亩油菜、200多亩葵花等，保证在春、夏、秋三季不同的时段都有鲜花盛开。</section><section><br/></section><p><img class="rich_pages" data-ratio="0.66171875" data-s="300,640" src="https://images.mediarank.cn/FsktqG10o7jmA69mYYlD6UW8CjOy" data-type="jpeg" data-w="1280"/></p><section><br/></section><section>纵穿全乡的10公里路两旁、每一条通村通社路旁，都因地制宜精心修建了小花园。乡负责人告诉记者:“这里，种上了八瓣梅、金盏花等好几种花草，值得高兴的是村民们都积极响应乡政府的号召自觉种花。”</section><section><br/></section><p><img class="rich_pages" data-ratio="0.66171875" data-s="300,640" src="https://images.mediarank.cn/FiRW-6bEHSDZNiI4ycEdlSv9QM3t" data-type="jpeg" data-w="1280"/></p><section><br/></section><section>河西乡的庄稼种得早，熟的也早，花也开的早，过不了一个月，这里就会成为花的海洋。</section><section><p><br/></p></section><section><p><img data-ratio="0.8780487804878049" src="https://images.mediarank.cn/FkvMEcWpXwj6wjL6zN7DmM_0GxNj" data-type="gif" data-w="41"/></p><section><section><p><strong><span><span>四季鲜果等您品尝</span></span></strong></p></section></section><section><p><img data-ratio="0.8780487804878049" src="https://images.mediarank.cn/FmBWdkQuFCb0xgmkPEh9CKTpxzf4" data-type="gif" data-w="41"/></p></section></section><section>  </section><p><span>春天，河西乡处处孕育着新希望。</span><span>记者在李家村瓜瓜子种植农民专业合作社看到当地的草莓已经成熟，已经有客人前来采摘；</span><span>新引进的四季梨、四季莲雾栽植成功，今年有望挂果，这将填补河西乡水果冬春断档的空白。</span></p><section><br/></section><section>河西乡俗称“喇嘛川”，过去，东乡县河滩川、永靖县白塔寺川、临夏县河西川合称“喇嘛三川”。喇嘛川瓜瓜子（小香瓜）自古有名。瓜瓜子种植农民专业合作负责人李永寿说：“我们成立的合作社就叫‘瓜瓜子’合作社，其目的就是要发扬光大先辈们留给我们的这一特产。去年，瓜瓜子熟了，兰州等外地和临夏市市民纷纷来这里采摘，说这辈子忘不了‘喇嘛川’的瓜瓜子！”</section><section><br/></section><p><img class="rich_pages" data-ratio="0.66171875" data-s="300,640" src="https://images.mediarank.cn/FivKl9Y1VbBFGbR1_veIL9-Yw_WU" data-type="jpeg" data-w="1280"/></p><section><br/></section><section>记者看到，温室的瓜瓜子秧苗已经长大，也开始种植在露天的地里。再过两个月，瓜瓜子就可以上市了。</section><section><br/></section><section>与瓜瓜子齐名的还有两道美味，就是“喇嘛川的菜瓜（番瓜）”和“喇嘛川的麦索（青稞）”。由于这里处于大夏河河谷地，这里的番瓜、青稞不仅品质好，而且早熟，村民们正在准备大片农田种植番瓜等蔬菜和青稞等农作物。</section><section><br/></section><section>有花必有果。“今年，这里栽植的各类优质水果树木有4000亩，无论什么时候来河西乡，一定会让客人一饱口福！”</section><section><br/></section><section>据介绍，自去年乡上通过环境整治，提升旅游基础设施，前来河西乡旅游的客人非常多，所有水果都卖上了好价钱。今年每个果农都拿出了管护果树的真本事，每一株果树都得到了精心管护。</section><section><br/></section><section><p><img data-ratio="0.8780487804878049" src="https://images.mediarank.cn/FkvMEcWpXwj6wjL6zN7DmM_0GxNj" data-type="gif" data-w="41"/></p><section><section><p><strong><span>欣赏风景感受自然</span></strong></p></section></section><section><p><img data-ratio="0.8780487804878049" src="https://images.mediarank.cn/FmBWdkQuFCb0xgmkPEh9CKTpxzf4" data-type="gif" data-w="41"/></p></section></section><section>    </section><section><span>到河西乡赏花、品尝果实、体验农家生活是现代人生活的美好向往和追捧的旅游新时尚，在这美丽的自然风景下体会浓浓的乡愁，让生活更精彩。</span></section><section><br/></section><section>河西乡利用得天独厚的优势，争取实施旅游基础设施项目，撩开河西风光神秘的面纱。</section><section><br/></section><p><img class="rich_pages" data-ratio="1.3333333333333333" data-s="300,640" src="https://images.mediarank.cn/FmnXwZkV0eZMhUlYP-ueml2eb8tr" data-type="jpeg" data-w="720"/></p><section><br/></section><section>河西乡桥窝村与东乡县河滩镇小庄村、东塬乡塔山村的交汇处，有临夏著名的景点——泄湖峡，民间又叫“野狐峡”。泄湖峡有着许多动人的传说，泄湖峡谷从老虎口至泄湖峡电厂尾水口全长约5公里，从老虎口至泄湖峡出口，落差达百米，河水湍急，以一泻千里之气势奔腾而下，气势尤为壮观。峡谷最深处约30米，最窄处约1米，两岸峭壁如削，巨石嶙峋，鬼斧神工。特别是夏、秋雨季，大夏河水以每秒上百立方米的流量，通过中间处仅1米的峡谷，汹涌澎湃，轰鸣如雷，令人惊心动魄。县乡规划在这里铺设栈道，让神秘的大夏河河谷向世人展示壮观的奇景。</section><section><br/></section><section>领略泄湖峡的壮观后，又有一处独特的景观——大夏河旱桥。大夏河冲出泄湖峡之后，又在厚厚的红土上冲出了一个洞，所有的河水穿洞而过，洞的上面被人们叫“旱桥”，新中国成立前几百年的时间里，旱桥是大夏河上唯一一座连接东西的桥。</section><section><br/></section><section>每年春天，刘家峡库区水面下降，露出大片耕地，两岸的农民开始抢种小麦和春油菜，秋天水面上涨便可以收获。常常由于水涨得快，不等庄稼完全收获，一大部分秸秆留在水里，成了黄河草鱼、白鲢鱼和鲤鱼的美食。目前，河岸上正在修栈道，以后可以在这里观赏鱼儿争食的景象。</section><section><br/></section><section><img class="rich_pages" data-ratio="0.66171875" data-s="300,640" src="https://images.mediarank.cn/FiMVOdRz2FgLbTVimxRiQmSf3NPN" data-type="jpeg" data-w="1280"/></section><section><br/></section><section>到河西最不能错过的就是刘家峡库区风光。已建成的长长的护岸平台上，建起了观光廊道，栽植了排排水柳。目前，这里的河岸工程已经复工建设，只等建好游览长廊，就能给游客一个亲近自然、亲近母亲河水的平台。</section><section><br/></section><p>春天的河西乡充满了希望的美、神秘的美，在这依山傍水间令人充满期望！（<strong>记者 </strong>马秀梅 赵怀斌 冯元鹏）</p><section><br/></section><section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section><section><br/></section></section><section><br/></section><section><strong><span>责编：</span></strong><span>范海东 <strong>编辑：</strong>山桦 <strong>校对：</strong>张皓静</span><br/></section><p><br/></p><p><img class="rich_pages __bg_gif" data-ratio="0.29984301412872844" data-type="gif" data-w="637" src="https://images.mediarank.cn/Fiz1wLtrZVy6lbggOsVR49lWx7es"/></p><p><img class="rich_pages" data-ratio="0.5125" data-s="300,640" data-type="jpeg" data-w="1280" src="https://images.mediarank.cn/Frrmn-JjFVFkt118SFmawAbPGDhe"/></p> </div>',
    #     '■编辑：阿水 || 新闻热线：96009999市发展改革委、市社会信用信息中心积极开展企业信用预警服务，定期推送企业信用预警和提醒信息，把企业失信问题解决在萌芽状态，减少企业严重失信行为发生，助力企业造诚实守信的社会氛围，积极推进诚信泰安建设，擦亮"信用泰安"品牌。泰安日报社·最泰安全媒体记者：王玉',
    #     '■编辑：阿水 || 新闻热线：96009999　3月24日，省委常委、省军区司令员邱月潮来泰调研民兵参加企业复工复产、森林防火和境外疫情输入防控等工作。市委书记崔洪刚陪同调研。　　　邱月潮一行先后来到常委、秘书长李灿玉，泰安军分区副司令员吴伟、任建宙参加有关活动。泰安日报社·最泰安全媒体记者：李庆林',
    #     '■编辑：阿水 || 新闻热线：96009999“这种‘不见面’的技术审查，不仅有效减少了人员聚集流动，而且充分保障了项目的审批质量不减、审批速度更快。”日前，在市行政审批服务局召开的市徂汶净水厂建设项力把耽误重大项目开工的时间抢回来。”市行政审批服务局局长宋鸿鹏说。泰安日报社·最泰安全媒体记者：王玉',
    # ]
    # for content in text_list:
    #     reporters = extract_reporters(content)
    #     print('-' * 20)
    #     print(f'记者: {reporters}')

    # ali_cli = aliyun_db.get_official_product_cli()
    ali_cli = aliyun_db.get_unofficial_test_cli()

    # query = MatchAllQuery()
    # sort = Sort(sorters=[FieldSort('updated_at', SortOrder.DESC)])
    query = TermsQuery('id', [
        1585201391905000, 1585201263225000, 1585201457184000, 1585201464247000,
        1585201549304000, 1585201883337000, 1585201889043000, 1585201893555000,
        1585202558417000, 1585196031849000
    ])
    rows, next_tk, total_count, is_all_succeed = ali_cli.search(
        'news', 'news_index', SearchQuery(query=query, get_total_count=True),
        ColumnsToGet(column_names=['content', 'origin_url'],
                     return_type=ColumnReturnType.SPECIFIED))
    for row in rows:
        content = row[1][0][1]
        reporters = extract_reporters(content)
        #print(row[1][1][1])
        print(f'记者: {reporters}')
        print('-' * 20)


# if __name__ == '__main__':
#     test_reporters()
