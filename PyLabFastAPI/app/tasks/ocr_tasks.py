# app/tasks/ocr_tasks.py
import json
import redis
import logging
# 引入适配器，用于在 Celery 中运行异步代码
from asgiref.sync import async_to_sync
from app.core.celery_app import celery_app
from app.utils.baidu_ocr import BaiduOCR
from app.models.user import TeacherProfile, User, UserRole
from tortoise import Tortoise
from app.config import settings

# 设置日志
logger = logging.getLogger(__name__)

# === 1. 初始化 Redis 客户端 ===
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


# === 2. 数据库连接辅助函数 ===
async def init_worker_db():
    # Worker 进程独立初始化 ORM
    await Tortoise.init(
        db_url=settings.DB_URL,
        modules={'models': ['app.models.user', 'app.models.course', 'app.models.oj']}
    )


async def close_worker_db():
    await Tortoise.close_connections()


# === 3. 真正的业务逻辑 (异步) - 保持原样 ===
async def process_ocr_logic(user_id: int, front_url: str, back_url: str):
    """
    执行 OCR 识别，更新数据库，自动升级角色，通过 Redis 发送通知
    """
    try:
        await init_worker_db()
        logger.info(f"[Worker] 正在处理用户 {user_id} 的 OCR 请求...")

        # 1. 查询档案
        profile = await TeacherProfile.filter(user_id=user_id).first()
        if not profile:
            logger.error(f"档案未找到: User {user_id}")
            return "Profile Not Found"

        # 2. 查询用户
        user = await User.filter(id=user_id).first()
        if not user:
            logger.error(f"用户未找到: User {user_id}")
            return "User Not Found"

        # 3. 调用百度 OCR (真实逻辑)
        # 注意：如果 BaiduOCR 内部用的是 requests (同步IO)，它会阻塞当前 loop，
        # 但在 async_to_sync + eventlet 模式下通常是可接受的。
        ocr = BaiduOCR()
        logger.info(f"🔍 [OCR] 正在请求百度云识别: {front_url}")

        # 假设 BaiduOCR.idcard_front 接收 URL 并返回字典
        id_info = ocr.idcard_front(front_url)

        notify_payload = {}

        if id_info:
            # --- A. 成功逻辑 ---
            profile.real_name = id_info["name"]
            profile.id_card = id_info["id_num"]
            profile.verify_status = 2  # 已认证

            # 自动升级角色
            if user.role == UserRole.STUDENT:
                user.role = UserRole.TEACHER
                await user.save()
                logger.info(f"🆙 用户 {user_id} 角色已自动升级为讲师")

            logger.info(f"✅ OCR 识别成功: {id_info['name']}")

            notify_payload = {
                "type": "ocr_result",
                "status": "success",
                "data": {
                    "user_id": user_id,
                    "real_name": id_info["name"],
                    "verify_status": 2,
                    "role": user.role.value
                }
            }
        else:
            # --- B. 失败逻辑 ---
            profile.verify_status = 3  # 被驳回
            profile.reject_reason = "图片识别失败，请确保文字清晰"
            logger.warning("❌ 识别失败，已驳回")

            notify_payload = {
                "type": "ocr_result",
                "status": "failed",
                "msg": "身份证识别失败，请重新上传清晰图片"
            }

        # 4. 更新图片 URL 并保存
        profile.id_card_img_f = front_url
        profile.id_card_img_b = back_url
        await profile.save()

        # === 4. 发送 WebSocket 通知 ===
        channel = f"notify:{user_id}"
        redis_client.publish(channel, json.dumps(notify_payload))
        logger.info(f"📨 [Worker] 通知已推送到: {channel}")

        return {"status": profile.verify_status, "user_id": user_id}

    except Exception as e:
        logger.error(f"❌ 任务异常: {e}", exc_info=True)
        # 发送错误通知
        error_payload = {
            "type": "ocr_result",
            "status": "error",
            "msg": f"系统处理异常: {str(e)}"
        }
        redis_client.publish(f"notify:{user_id}", json.dumps(error_payload))
        raise e
    finally:
        await close_worker_db()


# === 5. Celery 任务入口 (修改点) ===
@celery_app.task(name="ocr_task")
def verify_idcard_task(user_id: int, front_url: str, back_url: str):
    """
    使用 async_to_sync 桥接异步逻辑，完美兼容 Eventlet
    """
    # ❌ 不要用 asyncio.run()
    # ✅ 用 async_to_sync() 包装后调用
    run_sync = async_to_sync(process_ocr_logic)

    return run_sync(user_id, front_url, back_url)