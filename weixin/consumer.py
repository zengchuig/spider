import config,contextlib
from pymysql import connect
from kafka import KafkaConsumer

conn=connect(host='192.168.43.35',port=3306,user='root',password='222',database='request',charset='utf8')
@contextlib.contextmanager
def mysql():
    cs=conn.cursor()
    try:
        yield cs 
    finally:
        print('close')
        cs.close()
        conn.close()


consumer=KafkaConsumer(config.TOPIC,
                         bootstrap_servers=config.SERVER,
                         group_id='test',
                         auto_offset_reset='earliest')
with mysql() as cs:
	for msg in consumer:
		cs.execute(msg.value.decode())
		conn.commit()
		print(msg.value.decode())