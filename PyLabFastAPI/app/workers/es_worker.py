from app.models.course import Course
from app.services.es_sync import CourseESService
import logging

logger = logging.getLogger(__name__)


async def sync_course_task(msg: dict):
    """
    消费者回调函数：处理 ES 同步逻辑
    消息格式: {"id": 1, "action": "update" | "delete"}
    """
    course_id = msg.get("id")
    action = msg.get("action")

    if not course_id:
        return

    logger.info(f"🔧 [Worker] 开始处理: ID={course_id}, Action={action}")

    try:
        if action == "delete":
            await CourseESService.delete_course(course_id)

        elif action == "update":
            # 关键点：收到消息后，再去数据库查最新的状态
            # 这样避免了消息队列里的数据是旧的 (Stale Data)
            course = await Course.get_or_none(id=course_id)
            if course:
                await CourseESService.sync_course(course)
            else:
                # 查不到可能已经被删了，保险起见删一下 ES
                await CourseESService.delete_course(course_id)

    except Exception as e:
        logger.error(f"💥 [Worker] 同步发生异常: {e}")
        # 如果这里抛出异常，aio-pika 默认机制可能会重试或丢弃，取决于配置
        raise e