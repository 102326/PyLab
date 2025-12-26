# app/views/ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.socket_manager import ws_manager
import json
from app.models.chat import ChatMessage
# [新增] 引入推送工具
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

            if msg_data.get("type") == "chat":
                target_id = str(msg_data.get("to_user_id"))
                content = msg_data.get("content")

                if target_id and content:
                    # A. 存库
                    chat_msg = await ChatMessage.create(
                        sender_id=int(user_id),
                        receiver_id=int(target_id),
                        content=content
                    )

                    # B. 构造回传数据
                    payload = {
                        "type": "chat",
                        "from_user_id": int(user_id),
                        "content": content,
                        "time": chat_msg.created_at.strftime("%H:%M:%S")
                    }

                    # C. 尝试发送 (在线推送)
                    is_online = await ws_manager.send_personal_message(payload, target_id)

                    # D. [核心修改] 如果不在线 -> 触发离线 Web Push
                    if not is_online:
                        print(f"用户 {target_id} 不在线，正在转为离线推送...")
                        # 这里的 int(target_id) 确保类型匹配
                        await send_push_to_user(int(target_id), content, title="收到一条新消息")

    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)
    except Exception as e:
        print(f"WS Error: {e}")
        ws_manager.disconnect(user_id)