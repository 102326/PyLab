# PyLabFastAPI/app/models/chat.py
from tortoise import fields, models
import uuid


class ChatSession(models.Model):
    """
    会话表：相当于一个“聊天房间”
    """
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    user = fields.ForeignKeyField('models.User', related_name='sessions', description="所属用户")
    title = fields.CharField(max_length=100, default="新对话", description="会话标题")
    is_deleted = fields.BooleanField(default=False, description="逻辑删除")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "chat_sessions"
        ordering = ["-updated_at"]


class ChatMessage(models.Model):
    """
    消息表：存储每一句对话
    """
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    session = fields.ForeignKeyField('models.ChatSession', related_name='messages', index=True)
    role = fields.CharField(max_length=20, description="user/assistant/system")
    content = fields.TextField(description="对话内容")

    # 扩展字段：未来可以存 Token 消耗、引用来源等
    meta = fields.JSONField(null=True, default={})

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "chat_messages"
        ordering = ["created_at"]