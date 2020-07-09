import re
from pymysql import connect
from config import sql1,host,port,password,database,charset,user
conn=connect(host=host,port=port,user=user,password=password,database=database,charset=charset)
cs=conn.cursor()

article_list='mp/profile_ext?action=home'
article_content='mp.weixin.qq.com/s?__biz='
class A:
	def request(self,flow):
		if article_list in flow.request.url:
			print(55555555555555)
			param=flow.request.url.split('&')
			self.params={i.split('=',1)[0]:i.split('=',1)[1] for i in param[1:]}

	def response(self,flow):
		# if article_list in flow.request.url:
		# 	setcookie=flow.response.headers['Set-Cookie'].split(',')
		# 	setcookie=[i.split(';',1)[0] for i in setcookie]
		# 	setcookie={i.split('=',1)[0].strip():i.split('=',1)[1] for i in setcookie}
		# 	self.cookie.update(setcookie)
		# 	self.st=''
		# 	for k,v in self.cookie.items():
		# 		self.st+=str(k)+'='+str(v)+';'

		if article_content in flow.request.url:
			appmsg_token=re.search('var appmsg_token.*?"(.*?)"',flow.response.text,re.S).group(1)
			print(appmsg_token)
			sql='insert into req(params,cookie,appmsg_token) values("{}","","{}");'.format(self.params,appmsg_token)
			try:
				cs.execute(sql1)
				cs.execute(sql)
				conn.commit()
				cs.close()
				conn.close()
			except:
				cs.close()
				conn.close()
			print('--------------------------------')

addons=[A()]