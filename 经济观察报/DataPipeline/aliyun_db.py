from aliyun_table import TableClient
from tablestore import OTSClient

# tablestore配置
DB_INFO = {
    # 'end_point': 'https://nm-sea.cn-shenzhen.vpc.tablestore.aliyuncs.com',
'end_point': 'https://nm-sea.cn-shenzhen.ots.aliyuncs.com',
    'access_key_id': '',
    'access_key_secret': '',
}


def get_official_test_cli():
    """官方API，测试数据库，返回一个客户端连接

    使用官方API建议导入：from tablestore.metadata import *
    """
    return OTSClient(instance_name='tnm-sea', **DB_INFO)


def get_official_product_cli():
    """官方API，生产数据库，返回一个客户端连接

    使用官方API建议导入：from tablestore.metadata import *
    """
    return OTSClient(instance_name='nm-sea', **DB_INFO)


def get_unofficial_test_cli():
    """第三方库aliyun_table封装的API，测试数据库，返回一个客户端连接
    """
    return TableClient(instance_name='tnm-sea', **DB_INFO)


def get_unofficial_product_cli():
    """第三方库aliyun_table封装的API，生产数据库，返回一个客户端连接
    """
    return TableClient(instance_name='nm-sea', **DB_INFO)


if __name__ == "__main__":
    ali_cli = get_official_test_cli()
    print(ali_cli.list_table())
