# PyLabFastAPI/app/core/socket_manager.py
import asyncio
import logging
from typing import Dict
from fastapi import WebSocket
from redis import asyncio as aioredis
from app.config import settings

logger = logging.getLogger("uvicorn")


class ConnectionManager:
    def __init__(self):
        # 存放活跃连接: {user_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # ⚡️ 新增：存放后台监听任务: {user_id: asyncio.Task}
        self.redis_tasks: Dict[str, asyncio.Task] = {}

        # Redis 连接池
        self.redis = aioredis.from_url(settings.CELERY_BROKER_URL, encoding="utf-8", decode_responses=True)

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()

        # 如果该用户已有旧连接（比如快速刷新页面），先清理旧的
        await self.disconnect(user_id)

        self.active_connections[user_id] = websocket
        logger.info(f"🔌 User {user_id} connected via WebSocket")

        # ⚡️ 启动监听任务，并保存 Task 对象
        task = asyncio.create_task(self.listen_to_redis(user_id, websocket))
        self.redis_tasks[user_id] = task

    async def disconnect(self, user_id: str):
        """
        断开连接并清理资源
        """
        # 1. 移除 WebSocket 连接
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"🔌 User {user_id} disconnected from map")

        # 2. ⚡️ 强制取消后台 Redis 监听任务
        if user_id in self.redis_tasks:
            task = self.redis_tasks[user_id]
            task.cancel()  # 发送取消信号
            try:
                await task  # 等待任务真正结束
            except asyncio.CancelledError:
                logger.info(f"🛑 Redis listener for {user_id} cancelled successfully")
            del self.redis_tasks[user_id]

    async def send_personal_message(self, message: dict, to_user_id: str):
        """
        发送消息，返回是否发送成功
        """
        if to_user_id in self.active_connections:
            websocket = self.active_connections[to_user_id]
            try:
                await websocket.send_json(message)
                return True
            except Exception as e:
                logger.error(f"发送消息给 {to_user_id} 失败: {e}，正在清理连接...")
                # 发送失败说明 socket 已经断了，立即清理
                await self.disconnect(to_user_id)
                return False
        return False

    async def listen_to_redis(self, user_id: str, websocket: WebSocket):
        """
        监听 Redis 频道
        """
        pubsub = self.redis.pubsub()
        channel_name = f"notify:{user_id}"
        await pubsub.subscribe(channel_name)

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    # logger.debug(f"📨 Redis -> WS ({user_id}): {data}")
                    await websocket.send_text(data)
        except asyncio.CancelledError:
            # 任务被取消时，正常退出
            raise
        except Exception as e:
            logger.warning(f"Redis listener error for {user_id}: {e}")
        finally:
            # 确保退出时取消订阅
            await pubsub.unsubscribe(channel_name)
            await pubsub.close()


# 单例
ws_manager = ConnectionManager()