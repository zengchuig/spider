from kafka import KafkaProducer
import json,time,random,config,requests,re,contextlib
from queue import Queue
from pymysql import connect

producer=KafkaProducer(
bootstrap_servers=config.SERVER,
 value_serializer=lambda m: m.encode())


headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36 QBCore/4.0.1295.400 QQBrowser/9.0.2524.400 Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2875.116 Safari/537.36 NetType/WIFI MicroMessenger/7.0.5 WindowsWechat'}
session=requests.session()
conn=connect(host=config.host,port=config.port,user=config.user,password=config.password,database=config.database,charset=config.charset)

@contextlib.contextmanager
def mysql():
    cs=conn.cursor()
    try:
        yield cs 
    finally:
        print('close')
        cs.close()
        conn.close()


# 整理各url参数-------------------------
def get_params(appmsg_token=None,offset=None,content=None,read=None):
    notneed=['devicetype','version','lang','a8scene','winzoom']
    content_need=['key','uin','devicetype','version','lang','pass_ticket','winzoom']
    read_need=['key','uin','devicetype','pass_ticket','__biz']
    if read:
        params_=dict(mock='',appmsg_token=appmsg_token,wxtoken=777,clientversion='62080085',x5=0,f='json')
        for k,v in params.items():
            if k in read_need:
                params_[k]=v
        return params_
    if content:
        params_={}
        params_['ascene']=7
        for k,v in params.items():
            if k in content_need:
                params_[k]=v
        return params_
    if offset:
        params_=dict(action='getmsg',offset=offset,count=10,is_ok=1,wxtoken='',appmsg_token=appmsg_token,x5=0,f='json')
        for k,v in params.items():
            if k not in notneed:
                params_[k]=v
    else:
        params_={}
        params_['action']='home'
        for k,v in params.items():
            params_[k]=v
    return params_

def date(timestamp):
    timeArray = time.localtime(timestamp)
    date = time.strftime("%Y-%m-%d", timeArray)
    return date

# 将data整理，传给kafka--------------------------------------------
def parse(data):
    for i in data['list']:
        content=i['comm_msg_info']['content']
        timestamp=i['comm_msg_info']['datetime']
        time=date(timestamp)
        if not content:
            title=i['app_msg_ext_info']['title']
            digest=i['app_msg_ext_info']['digest']
            yuanchuang=i['app_msg_ext_info']['author']
            url=i['app_msg_ext_info']['content_url']
            SQL="insert into {}(title,digest,yuanchuang,time,url) values('{}','{}','{}','{}','{}');".format(config.name,title,digest,yuanchuang,time,url)
            producer.send(config.TOPIC,SQL)
        else:
            SQL="insert into {}(content,time) values('{}','{}')".format(config.name,content,time)
            producer.send(config.TOPIC,SQL)
    print('获取一组----------------------------------')

# 获取初始列表页，以及下拉列表页响应-------------------------------------
def get_resp(url,params,_json=None):
    resp=requests.get(url,params=params,headers=headers)
    if not _json:
        data=re.search("msgList.*?('.*?\]\}')",resp.text,re.S).group(1)
        data=eval(data.replace('&quot;','"'))
        data=eval(data)
        parse(data)
    else:
        data=resp.text
        data=json.loads(data)
        next_offset=data['next_offset']
        msg_count=data['msg_count']
        data=eval(data['general_msg_list'])
        parse(data)
        return next_offset,msg_count

def get_data(mid,sn,comment_id,req_id,pass_ticket):
    data={
        "r":                       '0.5161364069241767',
        "__biz":                   __biz,
        "appmsg_type":             9,
        "mid":                     mid,
        "sn":                      sn,
        "idx":                     1,
        "scene":                   38,
        "ct":                      1590669000,
        "abtest_cookie":           '',
        "devicetype":              "Windows 7",
        "version":                 62080085,
        "is_need_ticket":          0,
        "is_need_ad":              0,
        "comment_id":              comment_id,
        "is_need_reward":          0,
        "both_ad":                 0,
        "reward_uin_count":        0,
        "send_time":               '',
        "msg_daily_idx":           1,
        "is_original":             0,
        "is_only_read":            1,
        "req_id":                  req_id,
        "pass_ticket":             pass_ticket,
        "is_temp_url":             0,
        "item_show_type":          0,
        "tmp_version":             1,
        "more_read_type":          0,
        "appmsg_like_type":        2,
    }
    return data

def set_resp(func):
    def call_func(get_proxy,index,*args):
        i=1
        while i<=4:
            try:
                resp=func(index,*args)
            except Exception as ex:
                get_proxy.pop(index)
                time.sleep(1)
                i+=1
                print('i=',i)
                if i>=5:
                    print(ex)
                    raise err
                index=index if index<len(get_proxy) else 0
            else:
                index=index+1 if index<len(get_proxy)-1 else 0
                return resp,index
    return call_func

# 访问文章内容页面--------------------------------------------------
@set_resp
def get_resp1(index,*args):
    params_content,content_url=args
    # resp=requests.get(content_url,timeout=2,proxies={'http':'http://'+get_proxy[index]},params=params_content,headers=headers)
    resp=session.get(content_url,timeout=2,params=params_content,headers=headers)
    return resp

# 访问阅读数量url------------------------------------------------------
read_url='http://mp.weixin.qq.com/mp/getappmsgext'
@set_resp
def get_resp2(index,*args):
    params_read,data=args
    # resp=requests.post(read_url,timeout=2,proxies={'http':'http://'+get_proxy[index]},data=data,params=params_read,headers=headers).text
    resp=session.post(read_url,timeout=2,data=data,params=params_read,headers=headers).text
    return resp

def get_pagelist():
    # 访问初始页与下拉页，获取各个文章url等响应,并传给parse函数
    # 获取一次即可，后续可被注释------------------------------------
    url='https://mp.weixin.qq.com/mp/profile_ext'
    next_offset=10
    params_1=get_params()
    get_resp(url,params_1)
    while True:
        time.sleep(1)
        params_2=get_params(offset=next_offset)
        next_offset,msg_count=get_resp(url,params_2,_json=True)
        if msg_count<10:
            break

def get_queue():
    
    cs.execute('select id,url from {} where url is not Null and url!="" and id>=1;'.format(config.name))
    content_q=Queue()
    all_data=cs.fetchall()
    for i in all_data:
        content_q.put(i)
    return content_q    

def last_data():
    num=0
    # 获取代理ip
    # get_proxy=proxy.get_proxy().pro1
    get_proxy=[1]
    index=0
    while True:
        num+=1
        length=len(get_proxy)
        # time.sleep(2/length)
        time.sleep(3)
        _id,content_url=content_q.get()
        resp,index=get_resp1(get_proxy,index,params_content,content_url)
        index-=1
        try:
            # 正则过段时间可能会变化
            appmsg_token=re.search('window.appmsg_token.*?"(.*?)"',resp.text,re.S).group(1)
            req_id=re.search("req_id.*?'(.*?)'",resp.text,re.S).group(1)
            comment_id=re.search('comment_id.*?"(.*?)"',resp.text,re.S).group(1)
            fabuzhe=re.search('"js_name">(.*?)<',resp.text,re.S).group(1).strip()
            # fabuzhe=re.search('nick_name.*?"(.*?)"',resp.text,re.S).group(1).strip()
            # ct=re.search('var ct.*?"(.*?)"',resp.text,re.S).group(1)
        except:
            with open('log.html','w') as f:
                f.write(resp.text)
        sn=re.search('sn=(.*?)&',content_url).group(1)
        mid=re.search('mid=(.*?)&',content_url).group(1)
        pass_ticket=session.cookies.get_dict()['pass_ticket']
        data=get_data(mid,sn,comment_id,req_id,pass_ticket)

        params_read=get_params(read=True,appmsg_token=appmsg_token)
        resp,index=get_resp2(get_proxy,index,params_read,data)
        resp=json.loads(resp)

        like_num=resp['appmsgstat']['like_num']
        read_num=resp['appmsgstat']['read_num']
        SQL='update {} set fabuzhe="{}",like_num={},read_num={} where id={};'.format(config.name,fabuzhe,like_num,read_num,_id)
        producer.send(config.TOPIC,SQL)
        print(SQL)
        # cs.execute('update {} set fabuzhe="{}",like_num={},read_num={} where id={};'.format(config.name,fabuzhe,like_num,read_num,_id))
        if content_q.empty():
            break

with mysql() as cs:
    # table不存在则新建
    cs.execute(config.sql)
    # 从mysql获取mitm截取的参数,其实只有params中的key必需,短时间内有效-----------------------------------
    cs.execute("select params,cookie,appmsg_token from req")
    params,cookie,appmsg_token=cs.fetchall()[-1]
    params=eval(params)
    __biz=params['__biz']
    params_content=get_params(content=True)

    # 请求列表页，获取各文章url,交给kafka,获取一次即可，可持久保存
    if config.pagelist:
        get_pagelist()

    # 从DBMS取出所有url，id,入队列-----------------------------------------
    content_q=get_queue()
    # 获取最终数据，交给kafka
    last_data()


