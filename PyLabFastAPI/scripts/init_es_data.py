import sys
import os

# 将项目根目录加入路径，防止 ModuleNotFoundError
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from tortoise import Tortoise
from app.config import settings
from app.core.es import ESClient
from app.services.es_sync import CourseESService
from app.models.course import Course


async def main():
    print("🚀 开始全量同步数据到 ES...")

    # 1. 初始化数据库
    await Tortoise.init(
        db_url=settings.DB_URL,
        modules={"models": [
            "app.models.user",
            "app.models.course",
            "app.models.oj"
        ]}
    )

    # 2. 初始化 ES
    ESClient.init()

    # 3. 获取所有课程
    courses = await Course.all()
    print(f"📦 数据库中共有 {len(courses)} 门课程，准备同步...")

    # 4. 循环同步
    success_count = 0
    for course in courses:
        try:
            await CourseESService.sync_course(course)
            success_count += 1
        except Exception as e:
            print(f"❌ 同步失败 ID={course.id}: {e}")

    print(f"✅ 全量同步完成！成功: {success_count}/{len(courses)}")

    # 5. 关闭资源
    await ESClient.close()
    await Tortoise.close_connections()


if __name__ == "__main__":
    # Windows 下 asyncio 的常见问题修复
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())