# PyLabFastAPI/app/services/chat_service.py
import json
from uuid import UUID
from typing import List, Dict, Any
from datetime import datetime  # 👈 【修正1】使用 Python 标准库的时间
from redis.asyncio import Redis
from app.models.chat import ChatSession, ChatMessage
from app.models.user import User
from app.config import settings

# 初始化 Redis
redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)


class ChatService:
    CACHE_TTL = 3600 * 24  # 24小时

    @staticmethod
    def _get_cache_key(session_id: str) -> str:
        return f"chat:history:{session_id}"

    @classmethod
    async def create_session(cls, user: User, title: str = "新对话") -> ChatSession:
        return await ChatSession.create(user=user, title=title)

    @classmethod
    async def get_user_sessions(cls, user: User) -> List[ChatSession]:
        return await ChatSession.filter(user=user, is_deleted=False).all()

    @classmethod
    async def get_history(cls, session_id: UUID) -> List[Dict[str, Any]]:
        session_id_str = str(session_id)
        cache_key = cls._get_cache_key(session_id_str)

        # 1. 尝试从 Redis 获取
        cached_data = await redis.lrange(cache_key, 0, -1)
        if cached_data:
            return [json.loads(msg) for msg in cached_data]

        # 2. Redis 未命中，查数据库 (只取最近 50 条)
        db_msgs = await ChatMessage.filter(session_id=session_id) \
            .order_by("created_at") \
            .limit(50)

        history_list = []
        if db_msgs:
            # 3. 回填 Redis
            pipeline = redis.pipeline()
            for msg in db_msgs:
                msg_dict = {"role": msg.role, "content": msg.content}
                history_list.append(msg_dict)
                pipeline.rpush(cache_key, json.dumps(msg_dict))

            await pipeline.expire(cache_key, cls.CACHE_TTL)
            await pipeline.execute()

        return history_list

    @classmethod
    async def save_message(cls, session_id: UUID, role: str, content: str):
        session_id_str = str(session_id)

        # 1. 写入 DB
        await ChatMessage.create(session_id=session_id, role=role, content=content)

        # 2. 更新 Session 时间 (让它排到列表最前)
        # 👇 【修正2】使用 datetime.now()
        await ChatSession.filter(id=session_id).update(updated_at=datetime.now())

        # 3. 写入 Redis
        cache_key = cls._get_cache_key(session_id_str)
        msg_dict = {"role": role, "content": content}

        async with redis.pipeline() as pipe:
            await pipe.rpush(cache_key, json.dumps(msg_dict))
            await pipe.expire(cache_key, cls.CACHE_TTL)
            await pipe.execute()

    @classmethod
    async def clear_session(cls, session_id: UUID, user: User):
        """删除会话"""
        await ChatSession.filter(id=session_id, user=user).update(is_deleted=True)
        await redis.delete(cls._get_cache_key(str(session_id)))