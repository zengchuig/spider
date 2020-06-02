一：
输入mitmdump -q -s mitm.py命令。进入微信终端，点击1.png中历史消息，进入初始列表页，获取参数key、cookie，待后续使用。
然后随便点击个文章，获取响应中的appmsg_token，用于构造下拉url

二：
处理mysql，库与表结构可查看*.csv文件
使用的免费代理，爬取多页获取的有效ip数很可怜
运行wechat.py

___修改了_____
req中只有key才是关键
cookie可使用session
appmsg_token基本上永久有效,不同公众号key不共用