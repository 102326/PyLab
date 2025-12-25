启动消费者:
celery -A app.core.celery\_app worker -l info -P eventlet
