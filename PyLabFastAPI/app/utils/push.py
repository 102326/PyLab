# PyLabFastAPI/app/utils/push.py
import json
import asyncio
import os
from pywebpush import webpush, WebPushException
from app.models.user import User

# === 配置区域 ===
VAPID_PUBLIC_KEY = "BGctl8psYw3qvoEkdLWn1c2S8MSzOYCasxPIBbl6MK1wVpMegf77h_DVWh6tC15LvNmEFzMnKq4ky8Mi0N7O0vg"
VAPID_PRIVATE_KEY = "jbwnvEqv0JCBNNmRWlYSEbYXn9D88xg28QNfbuyPwqw"
VAPID_MAILTO = "mailto:admin@example.com"

# === 代理配置 ===
PROXY_URL = "http://127.0.0.1:7897"  # 请确保端口号正确


def _sync_send(subscription_info, message_body):
    """
    基础发送函数 (同步阻塞)
    """
    # 设置环境变量以使用代理
    os.environ["HTTP_PROXY"] = PROXY_URL
    os.environ["HTTPS_PROXY"] = PROXY_URL

    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(message_body),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_MAILTO},
            timeout=30
        )
        print("✅ [WebPush] 推送发送成功")
        return True
    except WebPushException as ex:
        # === [核心修复] 更暴力的 410 检测 ===
        # 有时候 ex.response.status_code 没取到，我们就查报错信息里的字符串
        msg = str(ex)
        is_gone = False

        if ex.response is not None and ex.response.status_code == 410:
            is_gone = True
        elif "410" in msg or "Gone" in msg or "expired" in msg.lower():
            is_gone = True

        if is_gone:
            print("⚠️ [WebPush] 订阅已失效 (410 Gone) -> 标记清理")
            return "GONE"

        print(f"❌ [WebPush] 发送失败: {ex}")
        return False
    except Exception as e:
        print(f"❌ [WebPush] 网络/未知错误: {e}")
        return False
    finally:
        # 清理环境变量
        os.environ.pop("HTTP_PROXY", None)
        os.environ.pop("HTTPS_PROXY", None)


async def send_push_to_user(target_user_id: int, content: str, title: str = "新消息"):
    user = await User.get_or_none(id=target_user_id)
    if not user or not user.push_subscriptions:
        return

    print(f"🚀 正在给用户 {target_user_id} 进行离线推送 (通过代理)...")

    payload = {
        "title": title,
        "body": content,
        "url": "/chat/user"
    }

    new_subs = []
    has_change = False

    for sub in user.push_subscriptions:
        # 执行发送
        res = await asyncio.to_thread(_sync_send, sub, payload)

        # 如果返回 GONE，说明这个订阅废了，不要加回 new_subs 列表 -> 相当于删除了
        if res == "GONE":
            has_change = True
            continue

        new_subs.append(sub)

    # 更新数据库，移除失效订阅
    if has_change:
        user.push_subscriptions = new_subs
        await user.save()
        print(f"♻️ 已清理用户 {target_user_id} 的无效订阅，剩余有效设备: {len(new_subs)}")