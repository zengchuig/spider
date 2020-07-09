import config,contextlib
from pymysql import connect
from kafka import KafkaConsumer

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


consumer=KafkaConsumer(config.TOPIC,
                         bootstrap_servers=config.SERVER,
                         group_id='test',
                         auto_offset_reset='earliest')
with mysql() as cs:
	for msg in consumer:
		cs.execute(msg.value.decode())
		conn.commit()
		print(msg.value.decode())