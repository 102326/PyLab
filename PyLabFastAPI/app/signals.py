from tortoise.signals import post_save, post_delete
from app.models.course import Course
from app.core.mq import RabbitMQClient  # 👈 改用 MQ 客户端

# 监听保存/更新 -> 发送 update 消息
@post_save(Course)
async def on_course_save(sender, instance, created, using_db, update_fields):
    await RabbitMQClient.publish({
        "id": instance.id,
        "action": "update"
    })

# 监听删除 -> 发送 delete 消息
@post_delete(Course)
async def on_course_delete(sender, instance, using_db):
    await RabbitMQClient.publish({
        "id": instance.id,
        "action": "delete"
    })