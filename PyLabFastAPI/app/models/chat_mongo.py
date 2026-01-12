# PyLabFastAPI/app/models/chat_mongo.py
from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional, Dict, Any
import uuid


class MongoChatMessage(Document):
    """
    AI Agent 聊天记录 (存储在 MongoDB)
    用于存储用户与 AI Agent 的对话历史。
    """
    # session_id: 对应 PostgreSQL 中的 chat_session_id 或前端生成的 UUID
    session_id: str = Field(..., description="会话ID")
    role: str  # user / assistant / system
    content: str

    # 灵活字段：可存储 token_usage, 响应耗时, 引用来源(rag_sources) 等
    meta: Dict[str, Any] = {}

    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "ai_chat_messages"
        # 索引优化：通常按会话ID拉取历史，按时间排序
        indexes = [
            "session_id",
            [("session_id", 1), ("created_at", 1)]
        ]


class MongoPrivateMessage(Document):
    """
    用户私信 (User-to-User) (存储在 MongoDB)
    用于存储用户之间的即时通讯消息。
    """
    sender_id: int
    receiver_id: int
    content: str

    # 消息类型: text, image, audio, video, file
    msg_type: str = "text"
    is_read: bool = False

    # 扩展字段：
    # audio -> {duration: 10, url: "..."}
    # image -> {width: 800, height: 600, url: "..."}
    extra: Dict[str, Any] = {}

    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "user_private_messages"
        indexes = [
            "sender_id",
            "receiver_id",
            # 复合索引：优化查询 "我与某人的聊天记录" (双向查询通常由应用层处理或存两份，这里先建基础索引)
            [
                ("sender_id", 1),
                ("receiver_id", 1),
                ("created_at", -1)
            ]
        ]