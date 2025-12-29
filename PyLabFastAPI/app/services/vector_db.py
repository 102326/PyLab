# PyLabFastAPI/app/services/vector_db.py
import httpx
from tortoise import fields, models


class VectorDBService:
    # 配置 Ollama 地址 (确保你本地装了 ollama 且 pull 了 nomic-embed-text)
    OLLAMA_URL = "http://localhost:11434/api/embeddings"
    MODEL_NAME = "nomic-embed-text"

    @classmethod
    async def get_embedding(cls, text: str):
        """
        调用本地 Ollama 生成向量
        """
        if not text:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    cls.OLLAMA_URL,
                    json={
                        "model": cls.MODEL_NAME,
                        "prompt": text
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("embedding")
                else:
                    print(f"⚠️ Ollama Error: {response.text}")
                    return None
        except Exception as e:
            print(f"❌ 连接 Ollama 失败: {e}")
            return None

    # === [核心修复] 新增了 update_course_embedding 方法 ===
    @classmethod
    async def update_course_embedding(cls, course_id: int, title: str, desc: str):
        """
        [后台任务] 生成课程向量并存入数据库
        """
        print(f"🧠 [AI] 正在为课程 {course_id} 生成向量索引...")

        # 1. 拼接文本 (标题 + 简介)
        text = f"{title} {desc or ''}"

        # 2. 获取向量
        embedding = await cls.get_embedding(text)

        if not embedding:
            print(f"⚠️ 课程 {course_id} 向量生成失败，跳过索引")
            return

        from app.models.course import Course
        conn = Course._meta.db

        try:
            # 3. 使用原生 SQL 更新
            # 因为 embedding 字段是通过 ALTER TABLE 加的，Tortoise 模型里没有定义它
            # pgvector 接受字符串格式的数组: '[0.1, 0.2, ...]'
            embedding_str = str(embedding)

            sql = f"UPDATE courses SET embedding = '{embedding_str}' WHERE id = {course_id}"
            await conn.execute_query(sql)
            print(f"✅ 课程 {course_id} 向量索引构建完成")
        except Exception as e:
            print(f"❌ 向量存入数据库失败: {e}")

    @classmethod
    async def init_vector_column(cls):
        """
        初始化数据库向量字段 (pgvector)
        """
        from app.models.course import Course

        conn = Course._meta.db
        try:
            # 1. 启用插件
            await conn.execute_query("CREATE EXTENSION IF NOT EXISTS vector;")

            # 2. 添加字段 (如果不存在)
            # 注意: 维度必须匹配模型! nomic-embed-text 是 768
            await conn.execute_query(
                "ALTER TABLE courses ADD COLUMN IF NOT EXISTS embedding vector(768);"
            )
            print("✅ 向量数据库字段检查完成")
        except Exception as e:
            print(f"⚠️ 初始化向量字段跳过 (可能已存在或不支持): {e}")

    @classmethod
    async def search_similar_courses(cls, query_text: str, limit: int = 5):
        """
        向量搜索
        """
        embedding = await cls.get_embedding(query_text)
        if not embedding:
            return []

        from app.models.course import Course
        conn = Course._meta.db

        # 使用 <=> (余弦距离) 排序
        embedding_str = str(embedding)
        sql = f"""
            SELECT id, title, "desc", cover, price,
                   embedding <=> '{embedding_str}' as distance
            FROM courses
            ORDER BY distance ASC
            LIMIT {limit};
        """

        try:
            results = await conn.execute_query_dict(sql)
            return results
        except Exception as e:
            print(f"❌ 向量搜索失败: {e}")
            return []