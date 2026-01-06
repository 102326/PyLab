# PyLabFastAPI/scripts/seed_oj_data.py
import asyncio
from tortoise import Tortoise
from app.config import settings
from app.models.user import User
from app.models.course import Course, Chapter, Lesson
from app.models.oj import Problem


async def init():
    # 1. 连接数据库
    # [修正] 这里使用 settings.DB_URL
    await Tortoise.init(
        db_url=settings.DB_URL,
        modules={"models": ["app.models.user", "app.models.course", "app.models.oj"]}
    )

    print("🌱 开始生成测试数据...")

    # 2. 获取或创建一个讲师用户
    teacher = await User.first()
    if not teacher:
        # 如果还没用户，创建一个测试用户
        from app.utils.security import get_password_hash
        teacher = await User.create(
            username="teacher",
            password_hash=get_password_hash("123456"),
            nickname="测试讲师",
            role=1
        )
        print("✅ 创建了测试用户: teacher / 123456")

    # 3. 创建一道题目
    problem = await Problem.create(
        title="挑战：打印 Hello World",
        slug="hello-world",
        content="""
# 题目描述
请使用 Python 输出一行字符串：`Hello World`。

### 输入格式
无

### 输出格式
一行字符串 `Hello World`
        """,
        init_code="print('Hello World')",
        time_limit=1000,
        memory_limit=128
    )
    print(f"✅ 题目创建成功: ID={problem.id}")

    # 4. 创建一门课程
    course = await Course.create(
        teacher=teacher,
        title="Python 极速入门 (OJ版)",
        desc="这是一门带有编程练习的测试课程，请尝试完成第二节的练习。",
        price=0,
        is_published=True,
        cover="https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=800&q=80"
    )
    print(f"✅ 课程创建成功: ID={course.id}")

    # 5. 创建章节
    chapter = await Chapter.create(course=course, title="第一章：环境搭建", rank=1)

    # 6. 创建课时
    # 第一节：视频
    await Lesson.create(
        chapter=chapter,
        title="欢迎来到 Python 世界",
        type="video",
        rank=1
    )

    # 第二节：练习 (关联上面的 Problem)
    await Lesson.create(
        chapter=chapter,
        title="动手试一试",
        type="problem",
        rank=2,
        problem_id=problem.id
    )
    print(f"✅ 课时创建成功：已关联题目 ID={problem.id}")
    print("🎉 数据注入完毕！请重启后端服务。")


if __name__ == "__main__":
    asyncio.run(init())