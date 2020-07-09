# 定义存储数据的table名字
name='yckjpl'

# 是否需要获取文章url
pagelist=False

# kafka配置
SERVER='localhost'
TOPIC='test1'

# mysql配置
host='192.168.43.35'
port=3306
user='root'
password='222'
database='request'
charset='utf8'

sql="""
CREATE TABLE if not exists {}(
  id smallint unsigned NOT NULL AUTO_INCREMENT,
  title varchar(255) CHARACTER SET utf8 DEFAULT NULL,
  read_num smallint unsigned DEFAULT NULL,
  like_num smallint unsigned DEFAULT NULL,
  yuanchuang varchar(20) CHARACTER SET utf8 DEFAULT NULL,
  fabuzhe varchar(30) CHARACTER SET utf8 DEFAULT NULL,
  time date DEFAULT NULL,
  url varchar(255) CHARACTER SET utf8 DEFAULT NULL,
  content text CHARACTER SET utf8,
  digest varchar(255) CHARACTER SET utf8 DEFAULT NULL,
  PRIMARY KEY (id)
)ENGINE=InnoDB;
""".format(name)

sql1="""
CREATE TABLE if not exists req (
  id smallint unsigned NOT NULL AUTO_INCREMENT,
  params text,
  cookie text,
  appmsg_token varchar(160) DEFAULT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8"""


