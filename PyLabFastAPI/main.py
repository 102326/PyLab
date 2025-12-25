from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from app.config import settings
from app.views.auth import router as auth_router
from app.views.media import router as media_router
from app.views.course import router as course_router
from app.views import ws
app = FastAPI()

app.include_router(auth_router)
app.include_router(media_router)
app.include_router(course_router)
app.include_router(ws.router, tags=["WebSocket"])
# 注册数据库 (PGSQL)
register_tortoise(
    app,
    db_url=settings.DB_URL,
    modules={"models": ["app.models.user",
                        "app.models.course",
                        "app.models.oj",
                        ],
             },
    generate_schemas=True, # 开发环境自动建表
    add_exception_handlers=True,
)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)