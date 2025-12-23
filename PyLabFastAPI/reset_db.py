# reset_db.py
from tortoise import Tortoise, run_async
from app.config import settings


async def init():
    # 连接数据库
    await Tortoise.init(
        db_url=settings.DB_URL,
        modules={"models": ["app.models.user",
                            "app.models.course",
                            "app.models.oj",
                            ]}
    )
    # 暴力生成 Schema (safe=False 表示如果有冲突可能会尝试处理，但在 Tortoise 中
    # 通常最好的重置方法是 generate_schemas(safe=False) 配合手动 Drop)

    # 既然连不上，我们直接执行 SQL 删表
    conn = Tortoise.get_connection("default")
    print("正在删除旧表...")
    try:
        await conn.execute_script("DROP TABLE IF EXISTS social_accounts;")
        await conn.execute_script("DROP TABLE IF EXISTS users;")
        print("旧表删除成功！")
    except Exception as e:
        print(f"删除表时出错 (可能表本就不存在): {e}")

    print("正在重新生成表结构...")
    await Tortoise.generate_schemas()
    print("数据库重置完成！")


if __name__ == "__main__":
    run_async(init())