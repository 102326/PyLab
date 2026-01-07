# PyLabFastAPI/app/views/ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.socket_manager import ws_manager
import json
# 1. 引入 PrivateMessage (用户私信表)
from app.models.chat import PrivateMessage
from app.utils.push import send_push_to_user

router = APIRouter()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            data_str = await websocket.receive_text()
            if data_str == "ping":
                await websocket.send_text("pong")
                continue

            try:
                msg_data = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            # 处理聊天消息
            if msg_data.get("type") == "chat":
                target_id = str(msg_data.get("to_user_id"))
                content = msg_data.get("content")

                if target_id and content:
                    try:
                        # A. 【核心修改】存入 PrivateMessage 表 (而不是 ChatMessage)
                        # 注意：Tortoise ORM 使用 sender_id 和 receiver_id
                        chat_msg = await PrivateMessage.create(
                            sender_id=int(user_id),
                            receiver_id=int(target_id),
                            content=content
                        )

                        # B. 构造回传数据
                        payload = {
                            "type": "chat",
                            "from_user_id": int(user_id),
                            "content": content,
                            # 格式化时间
                            "time": chat_msg.created_at.strftime("%H:%M:%S")
                        }

                        # C. 在线推送 (WebSocket)
                        is_online = await ws_manager.send_personal_message(payload, target_id)

                        # D. 离线推送 (APP Push)
                        if not is_online:
                            print(f"用户 {target_id} 不在线，转为离线推送...")
                            await send_push_to_user(int(target_id), content, title="收到新私信")

                    except Exception as e:
                        print(f"保存消息失败: {e}")

    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)
    except Exception as e:
        print(f"WS Error: {e}")
        ws_manager.disconnect(user_id)