# app/core/celery_app.py
import os
import sys

# =========================================================
# 🛑 [必须放第一行] Eventlet Monkey Patch
# 解决 Windows + Eventlet 环境下 socket/ssl 冲突导致的网络中断
# =========================================================
if sys.platform == "win32":
    try:
        import eventlet
        eventlet.monkey_patch()
    except ImportError:
        pass

# =========================================================
# 正常的导入逻辑
# =========================================================
from celery import Celery
from app.config import settings  # 引用你的 config

# 初始化 Celery 实例
celery_app = Celery(
    "pylab_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# 加载配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    # 降低心跳频率防止假死 (Windows下可选)
    broker_heartbeat=10,
)

# 自动发现任务
celery_app.autodiscover_tasks(["app.tasks.ocr_tasks"])