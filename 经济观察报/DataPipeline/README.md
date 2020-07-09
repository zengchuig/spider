# Pipelines

This Project provide pipelines for spiders to write data into database or 
message queue. and validate data fields recieved from spiders.

目前暂时只开放文章写入数据库的API：
请求：POST
URL：http://

## Configuration

Make sure you've installed python(>=3.6) correctly.

Install python requirements:

```
pip install -r requirements -i http://pypi.doubanio.com/simple/ --trusted-host pypi.doubanio.com
```

## Run

```py
# 测试环境（前台运行）
uvicorn main:app --host 0.0.0.0 --port 测试端口

# 生产环境（后台运行）
nohup uvicorn main:app --host 0.0.0.0 --port 6789 --reload > datapipeline.log 2>&1 &

# 进程查看
ps aux|grep main
```

Interface Redoc:

```
http://
```

Swagger Docs:

```
http://
```


## Table of contents

* [Todo](#user-content-todo)

* [Configuration](#user-content-configuration)

* [Run](#user-content-run)

* [File Manifest](#user-content-manifest)

* [Technologies](#user-content-technologies)

## Todo


- [x] Save or update article data.
- [ ] Get Article Categories.
- [ ] Get Article Tags.
- [ ] Get Article Reporters.
- [ ] Get Article Correspondents.
- [ ] Save or update media platform account data.
- [ ] Save or update comment data.





## Manifest

```
├── config.py               configs
├── examples.py             examples of interfaces
├── main.py                 api interface
├── models.py               api models
├── module                  
│   ├── db.py               database operations
│   └── __init__.py         other funtions
├── README.md               
├── requirements.txt        
├── start_cmd.txt           start commands
├── tasks.py                celery tasks
└── test.py

```


## Technologies

- python (>=3.6)

- celery

- fastapi

- tablestore


