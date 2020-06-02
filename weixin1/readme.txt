一：
输入mitmdump -q -s mitm.py 命令。进入微信终端，点击历史消息，进入初始列表页，获取参数key，因为先构造下拉页url,
还需要随便点击个文章，获取响应中的appmsg_token，用于构造下拉url

二：
shell脚本是kafka命令，需要自行修改

三:
consumer.py需要一直开启
每个公众号第一次运行需将config的pagelist=True,只要得到数据即可,不一定要全部得到，然后关闭pagelist,以后再次执行不用打开了

