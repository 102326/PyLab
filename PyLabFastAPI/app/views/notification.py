# PyLabFastAPI/app/views/notification.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.deps import get_current_user
from app.models.user import User
from pydantic import BaseModel
# [核心修改] 引入公共工具和密钥
from app.utils.push import VAPID_PUBLIC_KEY, _sync_send

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# === Pydantic 模型 ===
class PushKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionSchema(BaseModel):
    endpoint: str
    expirationTime: float | None = None
    keys: PushKeys


# === 1. 获取公钥接口 ===
@router.get("/vapid-public-key")
async def get_vapid_public_key():
    if not VAPID_PUBLIC_KEY:
        raise HTTPException(500, "后端 VAPID Key 未配置")
    return {"publicKey": VAPID_PUBLIC_KEY}


# === 2. 保存订阅信息接口 ===
@router.post("/subscribe")
async def subscribe(
        subscription: PushSubscriptionSchema,
        user: User = Depends(get_current_user)
):
    sub_data = subscription.model_dump(mode='json')

    # 获取当前订阅列表 (注意处理 None)
    current_subs = user.push_subscriptions or []

    # 简单查重：只对比 endpoint
    if not any(sub.get('endpoint') == sub_data.get('endpoint') for sub in current_subs):
        current_subs.append(sub_data)
        user.push_subscriptions = current_subs
        await user.save()
        print(f"✅ 用户 {user.username} ({user.id}) 新增设备订阅")

    return {"message": "Subscription saved"}


# === 3. 测试推送接口 ===
@router.post("/test-push")
async def test_push(
        background_tasks: BackgroundTasks,
        user: User = Depends(get_current_user)
):
    if not user.push_subscriptions:
        return {"message": "当前用户没有订阅任何设备，无法测试"}

    count = 0
    # 遍历该用户的所有设备进行推送
    for sub in user.push_subscriptions:
        # 使用 BackgroundTasks 把同步的发送任务丢到后台执行
        # 这里的 _sync_send 是从 app.utils.push 导入的
        background_tasks.add_task(
            _sync_send,
            sub,
            {
                "title": "测试推送",
                "body": "恭喜！这不仅是一条通知，更是离线推送配置成功的证明！🎉",
                "url": "/chat"
            }
        )
        count += 1

    return {"message": f"已触发推送任务，目标设备数: {count}"}