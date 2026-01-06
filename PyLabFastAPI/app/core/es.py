# app/core/es.py
from elasticsearch import AsyncElasticsearch
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class ESClient:
    _client: AsyncElasticsearch = None

    @classmethod
    def init(cls):
        """初始化 ES 连接"""
        if cls._client is None:
            cls._client = AsyncElasticsearch(settings.ES_URL)
            logger.info(f"✅ [ES] 已连接到 {settings.ES_URL}")

    @classmethod
    async def close(cls):
        """关闭连接"""
        if cls._client:
            await cls._client.close()
            cls._client = None
            logger.info("🛑 [ES] 连接已关闭")

    @classmethod
    def get(cls) -> AsyncElasticsearch:
        """获取客户端实例"""
        if cls._client is None:
            cls.init()
        return cls._client