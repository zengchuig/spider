#!/usr/bin/env python
# encoding: utf-8
import datetime
from scrapy.utils.project import get_project_settings
from lxml import etree
from qiniu import Auth, put_file
import requests
import hashlib
from aip import AipNlp
import time
import re


class tool(object):
    def __init__(self):
        self.q = Auth('x97-tNk8CSuuOP0l9XSi6SpC8xb_Rmmvh8R5xM5L',
                      'v6zUx3dOyRfRExP2FGGKws49_jXC9MWI4BKcOgII')
        self.bucket_name = 'niumedia'

    def rebuild_src(self, src,retry=1):
        # 上传到七牛后保存的文件名
        key = hashlib.md5(src.encode()).hexdigest() + '.png'
        # 生成上传 Token，可以指定过期时间等
        token = self.q.upload_token(self.bucket_name)
        # 请求获取图片
        r = requests.get(
            'http://img01.store.sogou.com/net/a/04/link?appid=100520029&url=' +
            src)
        try:
            r.raise_for_status()
            picname = 'test.png'
            with open(picname, 'wb') as f:
                f.write(r.content)
                f.close()
                # print("图片保存成功")
            # 传文件内容的接口
            info = put_file(token, key, picname)
            newsrc = 'https://images.mediarank.cn/' + str(info[0]['key'])
            return newsrc
        except:
            if retry <=2:
                retry += 1
                return self.rebuild_src(src,retry)
            else:
                print('qiniu_img_error:',"src:",src)
                return src



    def get_reporter_name(self, author_name):
        if not author_name:
            return ''
        reporter_name_list = []
        stop_words = [
            '文', '图', '作家', '作者', '记者', '驻', '摄影', '主编', '设计', '制图', '通讯',
            '编辑', '监制', '海报', '综合', '视频'
        ]
        for stop_word in stop_words:
            if stop_word in author_name:
                author_name = 'start' + author_name + 'end'
                pattern_list = [
                    re.compile(
                        r'(?:[作记]者|'
                        r'图、文\||图\||文、图\||文、图丨|图、文丨|图、文｜|文、图｜|文丨|文｜|文\||文 \| )'
                        r'([\s\S]+?)'
                        r'(?:图｜|图丨|图\||驻|摄影|主编|设计|制图|通讯|编辑|监制|海报|综合|视频|\u0001$|end)',
                        re.S),
                ]
                for pattern in pattern_list:
                    authors_str = re.findall(pattern, author_name)
                    for author_str in authors_str:
                        reporters = author_str.split(' ')
                        reporters = list(filter(None, reporters))
                        for reporter_name in reporters:
                            if len(reporter_name) < 2 or len(
                                    reporter_name
                            ) > 3 or '记者' in reporter_name or '作者' in reporter_name:
                                continue
                            else:
                                reporter_name_list.append(reporter_name)
                reporter_name_list = list(set(reporter_name_list))
                return reporter_name_list
        else:
            reporters = author_name.split(' ')
            reporters = list(filter(None, reporters))
            for reporter_name in reporters:
                if len(reporter_name) < 2 or len(
                        reporter_name
                ) > 3 or '记者' in reporter_name or '作者' in reporter_name:
                    continue
                else:
                    reporter_name_list.append(reporter_name)
            return reporter_name_list




    # 中央党校（国家行政学院）习近平新时代中国特色社会主义思想研究中心
    # TODO 如果是国家机构名称，作者名不要填，来源写 人民日报就好。 另外，如果 作者显示新华社记者 则需要将来源改为新华信。
    def check_authors(self,author_info_str,ori_medium_name):
        rem_list = ['未金梦','汪徐秋林','赋格','瓦当','美逸君','唐诗人','小引','弋舟','丽莎·格恩齐','猛犸','孜克热']
        rem_pass_list = ['中新社','南都','南周','楼主','公益','来信','花莲','台东','清博大',"文学院",'师范','金融','周刊','越众','系副','英文','中山','时局','嘉宾','乐评人','乐评','学院','代表','委员','首席', '学家','董事长','解读人']
        reporters = list()
        split_compile = re.compile(r"中山大学|哈佛大学|东吴大学|师范|文学院|复旦|教授|数据|支持|专家|；|;|,| 剪辑.*| |特约撰稿|特派记者|见习记者|记者|实习生|实习|、|，|电子报|\xa0|丨|/|图 / [\u4e00-\u9fa5]{2,4}|图文|文字|文案|插图|（.*?）|\(.*?\)|监制.*|制图：.*|摄影：|学者|作家|作者|译者|通讯员.*|读者来信|大学教师|历史所|历史学者|历史|经济|客户端|报道|网站|APP|app|媒体人|经纪人|文娱现场|文化观察|热点|诗人|医生|x|X|素材来源|：|:|研究员|北京|来自[\u4e00-\u9fa5]{2,}|发自[\u4e00-\u9fa5]{2,}|深圳|上海|杭州|南京|公司")
        # 特殊处理
        if 'Vyacheslav Prokofyev' in author_info_str:
            reporters.append('Vyacheslav Prokofyev')
        if 'Cindy Ord' in author_info_str:
            reporters.append('Cindy Ord')

        if ori_medium_name:
            author_info_str = author_info_str.replace('南方人物周刊徐梅','徐梅')

        author_infos = author_info_str.replace('贺欣香港大学法学院教授','贺欣').replace('\n','')
        author_infos = re.sub(r"图 ",'',author_infos)



        author_info_list = re.split(split_compile,author_infos)
        for auth in author_info_list:
            if re.match(r"^南方周末.*?",auth):
                ori_medium_name = '南方周末'
        if ori_medium_name:
            if '唐诗人' in author_info_str:
                reporters.append('唐诗人')
            for author_info in author_info_list:
                if not author_info or '文字' == author_info or author_info in rem_pass_list:
                    continue
                if author_info in rem_list:
                    reporters.append(author_info)
                    continue
                if '冯雨昕杜嘉禧' in author_info:
                    reporters.extend(['冯雨昕','杜嘉禧'])
                if 2 <= len(author_info) <= 4:
                    if self.check_name(author_info):
                        reporters.append(author_info)
                elif '·' in author_info or '.' in author_info or len(author_info) >=8:
                    author_info_result = self.get_chinese_name(author_info)
                    if author_info_result:
                        reporters.append(author_info_result)

        else:
            if '北京日报' in author_info_str:
                ori_medium_name = '北京日报'
            if '央视' == author_info_str:
                ori_medium_name = '央视网'
            if '21世纪' in author_info_str:
                ori_medium_name = '21世纪经济'
            author_len_3 = [i for i in author_info_list if len(i) >=2]
            ori_medium_name = self.check_ori(author_len_3, ori_medium_name)
        return list(set(reporters)),ori_medium_name


    def check_ori(self,author_list,ori_medium_name):
        if author_list:
            rem_pass_list = ['阿拉善SEE生态协会会长', '千篇一绿','小醉爸爸','21财经董鹏','24楼影院','新闻实验室']
            medium_name_3 = ['人民网','新华社', '今晚报', '市场报', '团结报', '青年报', '文学报', '书法报', '电脑报', '文汇报', '央视网','南方号','南方+','新华网','中新社','发改委','南都']
            for author_info in [author_list[0], author_list[-1]]:
                if '南都' in author_info:
                    ori_medium_name = '南都'
                    continue
                if ori_medium_name or '·' in author_info or '未' in author_info or not re.findall(r'[\d*\+\u4e00-\u9fa5]{3,}',author_info):
                    continue
                if len(author_info) ==3 and author_info in medium_name_3:
                    ori_medium_name = author_info
                if len(author_info) >= 4 and not self.check_name(author_info):
                    # 设置长度限制
                    ori_medium_name = author_info
                    if author_info in rem_pass_list or len(author_info) > 14:
                        ori_medium_name = ''
                        continue

        return ori_medium_name


    def check_name(self,name_str):
        pattern = r'^[赵|钱|孙|李|周|吴|郑|王|冯|陈|褚|卫|蒋|沈|韩|杨|朱|秦|尤|许|何|吕|施|张|孔|曹|严|华|金|魏|陶|姜|戚|谢|邹|喻|柏|水|窦|章|云|苏|潘|葛|奚|范|彭|郎|鲁|韦|昌|马|苗|凤|花|方|俞|任|袁|柳|酆|鲍|史|唐|费|廉|岑|薛|雷|贺|倪|汤|滕|殷|罗|毕|郝|邬|安|常|乐|于|时|傅|皮|卞|齐|康|伍|余|元|卜|顾|孟|平|黄|和|穆|萧|尹|姚|邵|湛|汪|祁|毛|禹|狄|米|贝|明|臧|计|伏|戴|谈|宋|茅|庞|熊|纪|舒|屈|项|祝|董|梁|杜|阮|蓝|闵|席|季|麻|强|贾|路|娄|危|江|童|颜|郭|梅|盛|林|刁|锺|徐|邱|骆|高|夏|蔡|田|樊|胡|凌|霍|虞|万|支|柯|昝|管|卢|莫|经|房|裘|缪|干|解|应|宗|丁|宣|贲|邓|郁|单|杭|洪|包|诸|左|石|崔|吉|钮|龚|程|嵇|邢|滑|裴|陆|荣|翁|荀|羊|於|惠|甄|麴|家|封|芮|羿|储|靳|汲|邴|糜|松|井|段|富|巫|乌|焦|巴|弓|牧|隗|山|谷|车|侯|宓|蓬|全|郗|班|仰|秋|仲|伊|宫|宁|仇|栾|暴|甘|钭|历|戎|祖|武|符|刘|景|詹|束|龙|叶|幸|司|韶|郜|黎|溥|印|宿|白|怀|蒲|邰|从|鄂|索|咸|籍|卓|蔺|屠|蒙|池|乔|阳|郁|胥|能|苍|双|闻|莘|党|翟|谭|贡|劳|逄|姬|申|扶|堵|冉|宰|郦|雍|却|桑|桂|濮|牛|寿|通|边|扈|燕|冀|浦|尚|农|温|别|庄|晏|柴|瞿|充|慕|连|茹|习|宦|艾|鱼|容|向|古|易|慎|戈|廖|庾|终|暨|居|衡|步|都|耿|满|弘|匡|国|文|寇|广|禄|阙|东|欧|沃|利|蔚|越|夔|隆|师|巩|厍|聂|晁|勾|敖|融|冷|訾|辛|阚|那|简|饶|空|曾|毋|沙|乜|养|鞠|须|丰|巢|关|蒯|相|荆|红|游|竺|权|司马|上官|欧阳|夏侯|诸葛|东方|赫连|皇甫|尉迟|公羊|澹台|濮阳|淳于|单于|太叔|申屠|公孙|仲孙|轩辕|令狐|钟离|宇文|长孙|慕容|司徒|司空|召|有|舜|岳|寸|贰|皇|侨|彤|竭|端|赫|实|甫|集|象|翠|狂|辟|典|良|函|苦|其|京|乌孙|完颜|富察|费莫|蹇|称|诺|来|多|繁|戊|朴|回|毓|鉏|税|荤|靖|绪|愈|硕|牢|买|但|巧|枚|撒|泰|秘|亥|绍|以|壬|森|斋|释|奕|姒|朋|求|羽|用|占|真|穰|翦|闾|漆|贵|代|贯|旁|崇|栋|告|休|褒|谏|锐|皋|闳|在|歧|禾|示|是|委|钊|频|嬴|呼|威|昂|律|冒|保|系|抄|定|化|莱|校|么|抗|祢|綦|悟|宏|功|庚|务|敏|捷|拱|兆|丑|丙|畅|苟|随|类|卯|俟|友|答|乙|允|甲|留|尾|佼|玄|乘|裔|延|植|环|矫|赛|昔|侍|度|旷|遇|偶|前|由|咎|塞|敛|受|泷|袭|衅|叔|圣|御|夫|仆|镇|藩|邸|府|掌|首|员|焉|戏|可|尔|凭|悉|进|笃|厚|仁|业|肇|资|合|仍|九|衷|哀|刑|俎|仵|圭|夷|徭|蛮|汗|孛|乾|帖|罕|洛|洋|邶|郸|郯|邗|邛|剑|虢|隋|菅|苌|树|桐|锁|钟|机|盘|铎|斛|玉|线|针|箕|庹|绳|磨|蒉|瓮|弭|刀|疏|牵|浑|恽|势|世|仝|同|蚁|止|戢|睢|冼|种|涂|肖|己|泣|潜|卷|脱|谬|蹉|赧|浮|顿|说|次|错|念|夙|斯|完|丹|表|聊|源|姓|吾|寻|展|不|户|闭|才|无|愚|性|雪|霜|烟|寒|字|桥|板|斐|诗|扬|善|揭|祈|析|赤|紫|青|柔|刚|奇|拜|佛|陀|弥|阿|素|长|僧|隐|仙|隽|宇|祭|酒|淡|塔|琦|闪|始|星|南|接|波|碧|速|禚|腾|潮|澄|潭|謇|纵|渠|奈|风|春|濯|沐|茂|英|兰|檀|藤|枝|检|生|折|驹|骑|貊|虎|肥|鹿|雀|野|禽|节|宜|鲜|粟|栗|豆|帛|官|布|衣|藏|宝|钞|银|门|盈|庆|喜|及|普|建|营|巨|望|希|道|载|声|犁|力|贸|勤|革|改|兴|亓|睦|信|闽|北|守|坚|勇|汉|练|尉|士|旅|令|将|旗|军|行|奉|敬|恭|仪|堂|丘|义|礼|慈|孝|理|伦|卿|问|永|辉|位|让|尧|依|犹|介|承|市|所|苑|杞|剧|第|零|谌|招|续|达|忻|鄞|战|迟|候|宛|励|粘|萨|邝|覃|辜|初|楼|城|区|局|台|原|考|妫|纳|泉|老|清|德|卑|过|麦|曲|竹|百|福|言|佟|爱|年|笪|谯|哈|墨|连|南宫|赏|伯|佴|佘|牟|商|西门|东门|左丘|梁丘|况|亢|缑|帅|微生|羊舌|海|归|呼延|东郭|百里|钦|鄢|汝|闫|楚|晋|谷梁|宰父|夹谷|拓跋|乐正|漆雕|公西|巫马|端木|颛孙|子车|督|仉|司寇|亓官|鲜于|盖|逯|库|郏|舍|逢|阴|薄|厉|稽|闾丘|公良|段干|开|光|瑞|眭|泥|运|摩|铁|迮|热娜|古丽|艾伯|乌图][\u4e00-\u9fa5]{1,2}$'
        result = re.findall(pattern, name_str)
        return result


    def gen_dates(self,b_date, days):
        day = datetime.timedelta(days=1)
        for i in range(days):
            yield b_date + day * i

    def get_date_list(self,beginDate, endDate):

        start = datetime.datetime.strptime(beginDate, "%Y%m%d")
        end = datetime.datetime.strptime(endDate, "%Y%m%d")
        data = list()
        for d in self.gen_dates(start, (end - start).days + 1):
            data.append(d)
        return data

    def get_time(self):
        # 爬取区间  %Y%m%d 形式
        beginDate = get_project_settings().get('CRAWL_TIME','20200603')
        endDate = time.strftime("%Y%m%d",time.localtime(time.time()))
        data = self.get_date_list(beginDate, endDate)
        for d in data:
            year = str(d.year)
            month = str(d.month) if d.month >= 10 else '0' + str(d.month)
            day = str(d.day) if d.day >= 10 else '0' + str(d.day)
            yield (year,month,day)

    def get_content(self, html):
        try:
            get_origin_img = re.findall(r'src="(.*?)"', html, re.S)
            # get_origin_img = list(filter( lambda i: not i.startswith("//imgcdn.yicai"),get_origin_img))
            # for im in get_origin_img:
            #     if '..' in im:
            #         img = "https://www.yicai.com/epaper/pc" + im.split("..")[-1].strip('.1')
            #     elif not im.startswith("http"):
            #         img = ''#'"https:" + im
            #     else:
            #         img = im
            if get_origin_img:
                for im in get_origin_img:
                    img_replace = self.rebuild_src(im)
                    html = html.replace(im, img_replace)
            return html
        except:
            return



if __name__ == '__main__':
    tools = tool()
    print(tools.check_authors('全国人大代表  张咏梅','xxxxxx'))



