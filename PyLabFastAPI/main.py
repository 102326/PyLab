from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference
from tortoise.contrib.fastapi import register_tortoise
from app.config import settings
from app.views.auth import router as auth_router
from app.views.media import router as media_router
from app.views.course import router as course_router
from app.views import ws
from tortoise import Tortoise
# 引入我们刚才写的向量服务
from app.views.chat import router as chat_router
from app.services.vector_db import VectorDBService
from app.views.notification import router as notification_router

app = FastAPI()

@app.get("/scalar", include_in_schema=False)  # 改这里！
async def scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )

# 1. 注册路由
app.include_router(auth_router)
app.include_router(media_router)
app.include_router(course_router)
app.include_router(ws.router, tags=["WebSocket"])
app.include_router(chat_router)
app.include_router(notification_router)
# 2. 注册数据库 (PGSQL)
# 注意：register_tortoise 会自动注册一个 "startup" 事件来连接数据库和生成表结构
register_tortoise(
    app,
    db_url=settings.DB_URL,
    modules={"models": ["app.models.user",
                        "app.models.course",
                        "app.models.oj",
                        "app.models.chat",
                        ],
             },
    generate_schemas=True, # 开发环境自动建表
    add_exception_handlers=True,
)

# === [核心修改] 新增启动钩子 ===
# 利用 FastAPI 的机制，这个函数会在 register_tortoise 完成数据库连接和建表之后执行
@app.on_event("startup")
async def init_vector_db():
    print("🚀 [Startup] 正在检查并初始化向量数据库字段...")
    # 这里调用我们在 vector_db.py 里写的暴力修改表结构的方法
    await VectorDBService.init_vector_column()
    print("✅ [Startup] 向量数据库初始化完成！")


if __name__ == '__main__':
    import uvicorn
    # 建议加上 workers=1 避免多进程导致开发环境日志混乱
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)