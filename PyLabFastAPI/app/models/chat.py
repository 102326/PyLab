# PyLabFastAPI/app/models/chat.py
from tortoise import fields, models
import uuid


# ==========================================
# Part 1: AI 会话 (Agent Chat)
# ==========================================

class ChatSession(models.Model):
    """
    AI 会话表：相当于一个“聊天房间”
    """
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    user = fields.ForeignKeyField('models.User', related_name='ai_sessions', description="所属用户")
    title = fields.CharField(max_length=100, default="新对话", description="会话标题")
    is_deleted = fields.BooleanField(default=False, description="逻辑删除")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "chat_sessions"
        ordering = ["-updated_at"]


class ChatMessage(models.Model):
    """
    AI 消息表：存储 AI 和用户的对话
    """
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    session = fields.ForeignKeyField('models.ChatSession', related_name='messages', index=True)
    role = fields.CharField(max_length=20, description="user/assistant/system")
    content = fields.TextField(description="对话内容")

    # 扩展字段
    meta = fields.JSONField(null=True, default={})
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "chat_messages"
        ordering = ["created_at"]


# ==========================================
# Part 2: 用户私信 (Private Chat) - 👈 新增/恢复的部分
# ==========================================

class PrivateMessage(models.Model):
    """
    私信表：用户对用户的点对点聊天
    """
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    # 使用 related_name 区分发送和接收
    sender = fields.ForeignKeyField('models.User', related_name='sent_private_msgs', description="发送者")
    receiver = fields.ForeignKeyField('models.User', related_name='received_private_msgs', description="接收者")

    content = fields.TextField(description="消息内容")
    is_read = fields.BooleanField(default=False, description="是否已读")

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "private_messages"
        ordering = ["created_at"]