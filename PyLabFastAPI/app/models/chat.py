# PyLabFastAPI/app/models/chat.py
from tortoise import fields, models


class ChatMessage(models.Model):
    """聊天消息表"""
    id = fields.IntField(pk=True)
    # 发送者 (关联 User 表)
    sender = fields.ForeignKeyField('models.User', related_name='sent_messages')
    # 接收者
    receiver = fields.ForeignKeyField('models.User', related_name='received_messages')

    content = fields.TextField(description="消息内容")
    # 消息类型: text, image, video... (目前先做 text)
    msg_type = fields.CharField(max_length=20, default="text")

    is_read = fields.BooleanField(default=False, description="是否已读")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "chat_messages"
        ordering = ["created_at"]


# AI 问答记录表
class AIChatRecord(models.Model):
    """AI 智能问答记录表"""
    id = fields.IntField(pk=True)

    # 关联到哪个用户
    user = fields.ForeignKeyField('models.User', related_name='ai_chats')

    # 用户的提问
    question = fields.TextField()

    # AI 的回答
    answer = fields.TextField()

    # 当时参考的上下文 (截取一部分存起来，方便回溯)
    sources = fields.TextField(null=True, description="RAG参考资料摘要")

    # 记录时间
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "ai_chat_records"
        ordering = ["-created_at"]  # 默认按时间倒序