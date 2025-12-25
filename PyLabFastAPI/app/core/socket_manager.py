# app/core/socket_manager.py
import asyncio
import json
import logging
from typing import Dict
from fastapi import WebSocket
from redis import asyncio as aioredis  # 使用异步 Redis 客户端
from app.config import settings

logger = logging.getLogger("uvicorn")


class ConnectionManager:
    def __init__(self):
        # 存放活跃连接: {user_id: WebSocket}
        # 实际生产中可能一个用户有多端登录，这里建议用 {user_id: [ws1, ws2]}
        self.active_connections: Dict[str, WebSocket] = {}
        # Redis 连接池
        self.redis = aioredis.from_url(settings.CELERY_BROKER_URL, encoding="utf-8", decode_responses=True)

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"🔌 User {user_id} connected via WebSocket")

        # 【核心逻辑】: 为每个连接启动一个独立的后台任务监听 Redis
        # 这样当 Celery 发消息到 Redis 时，FastAPI 能立马感知
        asyncio.create_task(self.listen_to_redis(user_id, websocket))

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"🔌 User {user_id} disconnected")

    async def listen_to_redis(self, user_id: str, websocket: WebSocket):
        """
        监听 Redis 中名为 'notify:{user_id}' 的频道
        """
        pubsub = self.redis.pubsub()
        channel_name = f"notify:{user_id}"
        await pubsub.subscribe(channel_name)

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    # 从 Redis 收到 Celery 的消息 -> 转发给前端
                    data = message["data"]
                    logger.info(f"📨 Redis -> WS ({user_id}): {data}")
                    await websocket.send_text(data)
        except Exception as e:
            logger.warning(f"Redis listener stopped for {user_id}: {e}")
        finally:
            await pubsub.unsubscribe(channel_name)


# 单例模式
ws_manager = ConnectionManager()