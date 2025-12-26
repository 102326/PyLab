# PyLabFastAPI/app/services/vector_db.py
import httpx
from tortoise.contrib.postgres.fields import ArrayField
from tortoise import fields, models


# 确保安装了 httpx: pip install httpx

class VectorDBService:
    # 配置 Ollama 地址
    OLLAMA_URL = "http://localhost:11434/api/embeddings"
    # 使用的模型名称 (确保你 ollama pull 过这个模型)
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
                    timeout=30.0  # 设置个超时时间
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("embedding")
                else:
                    print(f"⚠️ Ollama Error: {response.text}")
                    return None
        except Exception as e:
            print(f"❌ 连接 Ollama 失败: {e}")
            # 开发环境如果没开 ollama，可以返回一个全0向量防止报错，或者直接抛出
            return None

    @classmethod
    async def init_vector_column(cls):
        """
        初始化数据库向量字段 (pgvector)
        """
        from app.models.course import Course

        # 1. 确保安装了 vector 扩展
        conn = Course._meta.db
        await conn.execute_query("CREATE EXTENSION IF NOT EXISTS vector;")

        # 2. 检查字段是否存在 (简单粗暴版)
        # 注意：不同的模型维度不同！nomic-embed-text 是 768 维
        # 如果你之前用的是其他模型，可能需要删表重建或修改维度
        # ALTER TABLE courses ADD COLUMN IF NOT EXISTS embedding vector(768);
        try:
            # 这里维度写死 768 (nomic-embed-text 的维度)
            # 如果用 all-minilm 是 384
            await conn.execute_query(
                "ALTER TABLE courses ADD COLUMN IF NOT EXISTS embedding vector(768);"
            )
        except Exception as e:
            print(f"初始化向量字段警告: {e}")

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

        # 使用 <-> (L2距离) 或 <=> (余弦距离)
        # 注意：Tortoise ORM 原生不支持向量查询，这里直接写 SQL
        sql = f"""
            SELECT id, title, description, cover_img, 
                   embedding <=> '{embedding}' as distance
            FROM courses
            ORDER BY distance ASC
            LIMIT {limit};
        """

        results = await conn.execute_query_dict(sql)
        return results