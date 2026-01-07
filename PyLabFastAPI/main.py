# PyLabFastAPI/main.py
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
from app.core.mq import RabbitMQClient
from app.workers.es_worker import sync_course_task
logging.basicConfig(level=logging.INFO)

# === [核心改造] 定义生命周期管理器 ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 🟢 启动阶段 (Startup) ---
    print("🚀 [Lifespan] 系统启动中...")

    # 1. 连接数据库 (Tortoise ORM)
    #    手动初始化，确保在向量库操作前数据库已就绪
    await Tortoise.init(
        db_url=settings.DB_URL,
        modules={"models": [
            "app.models.user",
            "app.models.course",
            "app.models.oj",
            "app.models.chat",
        ]},
    )
    # 开发环境自动生成表结构 (生产环境请用 aerich 迁移工具)
    await Tortoise.generate_schemas()
    print("✅ [Database] PostgreSQL 连接成功 & 表结构已同步")

    # 2. 初始化向量数据库字段
    #    此时数据库已连接，可以安全操作
    try:
        await VectorDBService.init_vector_column()
    except Exception as e:
        print(f"⚠️ [VectorDB] 初始化警告: {e}")

    # 3. 初始化 Elasticsearch
    ESClient.init()
    try:
        await CourseESService.create_index()
    except Exception as e:
        print(f"⚠️ [ES] 索引初始化失败 (请检查 Docker): {e}")

    # 4. === [新增] RabbitMQ 初始化 & 启动消费者 ===
    #    启动 MQ 连接，并挂载消费者任务
    try:
        await RabbitMQClient.init()
        # 告诉 MQ：收到消息后，请调用 sync_course_task 函数处理
        await RabbitMQClient.consume(sync_course_task)
    except Exception as e:
        print(f"⚠️ [RabbitMQ] 启动失败 (请检查 Docker 5672 端口): {e}")

    # --- ⏸️ 应用运行中 (Yield) ---
    yield

    # --- 🔴 关闭阶段 (Shutdown) ---
    print("🛑 [Lifespan] 系统关闭中...")

    # 5. === [新增] 关闭 MQ 连接 ===
    await RabbitMQClient.close()

    # 6. 关闭 ES 连接
    await ESClient.close()

    # 7. 关闭数据库连接
    await Tortoise.close_connections()
    print("👋 [Lifespan] 资源已释放，再见！")


# === 初始化 FastAPI ===
# 将 lifespan 函数传给 FastAPI
app = FastAPI(lifespan=lifespan)

# 👇👇👇 2. [核心修复] 添加 CORS 中间件配置
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