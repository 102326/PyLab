# app/signals.py
from tortoise.signals import post_save, post_delete
from app.models.course import Course
from app.core.mq import RabbitMQClient

# 监听保存/更新 -> 发送 update 消息
@post_save(Course)
async def on_course_save(sender, instance, created, using_db, update_fields):
    # 修复点：必须指定 routing_key="task.course.sync"
    # 这样 main.py 里的消费者才能收到消息
    await RabbitMQClient.publish(
        routing_key="task.course.sync",
        message={
            "id": instance.id,
            "action": "update"
        }
    )

# 监听删除 -> 发送 delete 消息
@post_delete(Course)
async def on_course_delete(sender, instance, using_db):
    await RabbitMQClient.publish(
        routing_key="task.course.sync",
        message={
            "id": instance.id,
            "action": "delete"
        }
    )