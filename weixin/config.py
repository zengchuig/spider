name='yckjpl'
# 是否需要获取文章url
pagelist=False
SERVER='localhost'
TOPIC='test1'

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


# import contextlib
# @contextlib.contextmanager
# def aa():
# 	try:
# 		yield 15
# 	finally:
# 		print(2)
# with aa() as l:
# 	print(l)
# 	def a():
# 		print(3)
# 		pass
# 	a()

