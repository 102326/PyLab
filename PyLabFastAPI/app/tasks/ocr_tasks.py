# app/tasks/ocr_tasks.py
import asyncio
import json
import redis
from celery import Task
from app.core.celery_app import celery_app
from app.utils.baidu_ocr import BaiduOCR
# 引入 User 模型和 UserRole 枚举，用于修改角色
from app.models.user import TeacherProfile, User, UserRole
from tortoise import Tortoise
from app.config import settings

# === 1. 初始化 Redis 客户端 (用于发送通知) ===
# decode_responses=True 让取出的数据自动变成 str
redis_client = redis.from_url(settings.CELERY_BROKER_URL, decode_responses=True)


# === 2. 数据库连接辅助函数 ===
async def init_worker_db():
    # Worker 是独立进程，必须自己初始化 Tortoise ORM
    await Tortoise.init(
        db_url=settings.DB_URL,
        modules={'models': ['app.models.user', 'app.models.course', 'app.models.oj']}
    )


async def close_worker_db():
    await Tortoise.close_connections()


# === 3. 真正的业务逻辑 (异步) ===
async def process_ocr_logic(user_id: int, front_url: str, back_url: str):
    """
    执行 OCR 识别，更新数据库，自动升级角色，并通过 Redis 发送实时通知
    """
    try:
        await init_worker_db()
        print(f"[Worker] 正在处理用户 {user_id} 的 OCR 请求...")

        # 1. 查询档案
        profile = await TeacherProfile.filter(user_id=user_id).first()
        if not profile:
            print(f"档案未找到: User {user_id}")
            return "Profile Not Found"

        # 2. 查询用户 (为了修改 role)
        user = await User.filter(id=user_id).first()
        if not user:
            print(f"用户未找到: User {user_id}")
            return "User Not Found"

        # 3. 调用百度 OCR
        ocr = BaiduOCR()
        id_info = ocr.idcard_front(front_url)

        notify_payload = {}

        if id_info:
            # --- A. 成功逻辑 ---
            # 1. 更新档案信息
            profile.real_name = id_info["name"]
            profile.id_card = id_info["id_num"]
            profile.verify_status = 2  # 状态：已认证

            # 2. [核心] 自动升级用户角色
            # 如果是学生(0)，自动升级为老师(1)；如果是管理员(9)则不动
            if user.role == UserRole.STUDENT:
                user.role = UserRole.TEACHER
                await user.save()
                print(f"用户 {user_id} 角色已自动升级为讲师 (Role=1)")

            print(f"OCR 识别成功: {id_info['name']}")

            # 3. 准备成功通知消息 (WebSocket用)
            notify_payload = {
                "type": "ocr_result",
                "status": "success",
                "data": {
                    "user_id": user_id,
                    "real_name": id_info["name"],
                    "verify_status": 2,
                    "role": user.role.value  # 将最新的角色发给前端
                }
            }
        else:
            # --- B. 失败逻辑 ---
            profile.verify_status = 3  # 状态：被驳回
            profile.reject_reason = "图片识别失败，请确保文字清晰"
            print("识别失败，已驳回")

            # 准备失败通知消息
            notify_payload = {
                "type": "ocr_result",
                "status": "failed",
                "msg": "身份证识别失败，请重新上传清晰图片"
            }

        # 4. 无论成功失败，都更新图片 URL 并保存档案
        profile.id_card_img_f = front_url
        profile.id_card_img_b = back_url
        await profile.save()

        # === 4. 发送 WebSocket 通知 (Redis Pub/Sub) ===
        # 频道名必须和前端监听的保持一致: notify:{user_id}
        channel = f"notify:{user_id}"
        redis_client.publish(channel, json.dumps(notify_payload))
        print(f"[Worker] 通知已推送至 Redis 频道: {channel}")

        return {"status": profile.verify_status, "user_id": user_id}

    except Exception as e:
        print(f"任务异常: {e}")
        # 发生代码级异常，也通知前端
        error_payload = {
            "type": "ocr_result",
            "status": "error",
            "msg": "服务器处理任务时发生异常"
        }
        redis_client.publish(f"notify:{user_id}", json.dumps(error_payload))
        raise e
    finally:
        # 务必关闭数据库连接
        await close_worker_db()


# === 5. Celery 任务入口 ===
@celery_app.task(name="ocr_task")
def verify_idcard_task(user_id: int, front_url: str, back_url: str):
    """
    Celery Worker 调用的同步入口，内部使用 asyncio.run 驱动异步逻辑
    """
    return asyncio.run(process_ocr_logic(user_id, front_url, back_url))