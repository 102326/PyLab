# app/core/celery_app.py
from celery import Celery
from app.config import settings

# 1. 实例化 Celery
# "pylab_worker" 是 Worker 的名字，方便在日志里区分
celery_app = Celery(
    "pylab_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.ocr_tasks"]
)

# 2. 详细配置
celery_app.conf.update(
    # 序列化格式 (安全起见统一用 json)
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # 时区
    timezone="Asia/Shanghai",
    enable_utc=True,

    # === 优化配置 ===
    # 任务确认: 任务执行完且无报错，才在 Redis 中删除消息 (防止任务丢失)
    task_acks_late=True,
    # 预取限制: 防止一个 Worker 一次拿太多任务导致其他 Worker 闲置
    # 对于 OCR 这种耗时 1-2秒 的任务，设为 1 很合适
    worker_prefetch_multiplier=1,
    # 任务超时: 10分钟没跑完强制杀掉，防止卡死
    task_time_limit=600,
)