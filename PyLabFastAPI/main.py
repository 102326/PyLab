# PyLabFastAPI/main.py

from dotenv import load_dotenv
load_dotenv(override=True)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference
from tortoise import Tortoise
import logging
from app.config import settings
# 引入各个模块
from app.views.auth import router as auth_router
from app.views.media import router as media_router
from app.views.course import router as course_router
from app.views.chat import router as chat_router
from app.views.notification import router as notification_router
from app.views import ws
from app.views import oj
from app.views import ai
from fastapi.middleware.cors import CORSMiddleware
# 引入服务
from app.core.es import ESClient
from app.services.es_sync import CourseESService
from app.services.vector_db import VectorDBService
import app.signals  # 信号监听

# === [新增引入] MQ 客户端与消费者任务 ===
from app.workers.es_worker import sync_course_task
logging.basicConfig(level=logging.INFO)
from app.core.mq import RabbitMQClient

# === [核心改造] 定义生命周期管理器 ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 🟢 启动阶段 (Startup) ---
    print("🚀 [Lifespan] 系统启动中...")

    # 1. 数据库 (保持不变)
    await Tortoise.init(
        db_url=settings.DB_URL,
        modules={"models": ["app.models.user", "app.models.course", "app.models.oj", "app.models.chat"]},
    )
    await Tortoise.generate_schemas()
    print("✅ [Database] PostgreSQL 连接成功")

    # 2. 向量库 (保持不变)
    try:
        await VectorDBService.init_vector_column()
    except Exception as e:
        print(f"⚠️ [VectorDB] 初始化警告: {e}")

    # 3. ES (保持不变)
    ESClient.init()
    try:
        await CourseESService.create_index()
    except Exception as e:
        print(f"⚠️ [ES] 索引初始化失败: {e}")

    # 4. === [修正] RabbitMQ 初始化 & 启动消费者 ===
    try:
        # A. 连接 MQ (注意：是 connect 不是 init)
        await RabbitMQClient.connect()

        # B. 启动消费者 (必须指定 队列名 和 路由键)
        # 假设：只要是有 'task.course.sync' 路由键的消息，都由这个 task 处理
        await RabbitMQClient.consume(
            queue_name="q_course_sync",  # 队列名 (持久化存在 RabbitMQ 里)
            routing_key="task.course.sync",  # 发送消息时用的 Key
            callback_func=sync_course_task  # 你的业务函数
        )

    except Exception as e:
        print(f"⚠️ [RabbitMQ] 启动失败 (请检查 Docker): {e}")

    # --- ⏸️ 应用运行中 (Yield) ---
    yield

    # --- 🔴 关闭阶段 (Shutdown) ---
    print("🛑 [Lifespan] 系统关闭中...")

    # 5. 关闭 MQ
    await RabbitMQClient.close()

    # 6. 关闭其他资源 (保持不变)
    await ESClient.close()
    await Tortoise.close_connections()
    print("👋 [Lifespan] 资源已释放")


# === 初始化 FastAPI ===
# 将 lifespan 函数传给 FastAPI
app = FastAPI(lifespan=lifespan)

# 👇👇👇 2. [CORS 配置]
origins = [
    "http://localhost:5173",    # Vue 默认端口
    "http://127.0.0.1:5173",    # 以防万一
    "http://localhost:8080",    # 备用
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # ✅ 指定白名单
    allow_credentials=True,     # ✅ 允许带 Token/Cookie
    allow_methods=["*"],        # 允许所有方法 (POST, GET, OPTIONS...)
    allow_headers=["*"],        # 允许所有 Header
)
# === 注册文档路由 ===
@app.get("/scalar", include_in_schema=False)
async def scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )


# === 注册业务路由 ===
app.include_router(auth_router)
app.include_router(media_router)
app.include_router(course_router)
app.include_router(chat_router)
app.include_router(notification_router)
app.include_router(oj.router)
app.include_router(ai.router)
app.include_router(ws.router, tags=["WebSocket"])

if __name__ == '__main__':
    import uvicorn
    # 建议生产环境 worker>1，但在 RabbitMQ 消费者模式下
    # 多进程开发环境可能会导致重复消费日志，属于正常现象
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)