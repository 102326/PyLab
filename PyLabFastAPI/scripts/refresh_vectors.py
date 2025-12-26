# scripts/refresh_vectors.py
import sys
import os
import asyncio

# 将项目根目录加入 python path，防止找不到 app 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from app.config import settings
from app.models.course import Course
from app.services.vector_db import VectorDBService


async def main():
    print("🚀 开始为旧课程生成向量索引...")

    # 1. 初始化数据库
    await Tortoise.init(
        db_url=settings.DB_URL,
        modules={'models': ['app.models.user', 'app.models.course', 'app.models.oj']}
    )

    # 2. 获取所有已发布的课程
    courses = await Course.all()
    print(f"📦 发现 {len(courses)} 门课程，准备处理...")

    # 3. 逐个生成向量
    count = 0
    for course in courses:
        # 只要没有向量，或者是想强制刷新，都可以跑
        try:
            print(f"   -> 正在处理: 《{course.title}》")
            await VectorDBService.update_course_embedding(
                course.id,
                course.title,
                course.desc or ""
            )
            count += 1
        except Exception as e:
            print(f"❌ 课程 {course.id} 处理失败: {e}")

    print(f"\n✅ 全部完成！共更新 {count} 门课程的向量数据。")
    print("现在你可以去测试语义搜索了！")

    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())