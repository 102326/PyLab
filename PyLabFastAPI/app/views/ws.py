# app/views/ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.socket_manager import ws_manager
import json
from datetime import datetime
from app.models.chat import ChatMessage  # 引入模型

router = APIRouter()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            # 1. 接收前端消息
            data_str = await websocket.receive_text()

            # 心跳检测
            if data_str == "ping":
                await websocket.send_text("pong")
                continue

            # 2. 解析 JSON
            try:
                msg_data = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            # 3. 处理聊天消息
            if msg_data.get("type") == "chat":
                target_id = str(msg_data.get("to_user_id"))
                content = msg_data.get("content")

                if target_id and content:
                    # A. 【持久化】存入数据库 (必须步骤)
                    # 注意：这里 user_id 和 target_id 都是 str，存库时可能需要转 int
                    # 我们假设数据库 id 是 int
                    chat_msg = await ChatMessage.create(
                        sender_id=int(user_id),
                        receiver_id=int(target_id),
                        content=content
                    )

                    # B. 【转发】构造回传数据
                    payload = {
                        "type": "chat",
                        "from_user_id": int(user_id),
                        "content": content,
                        "time": chat_msg.created_at.strftime("%H:%M:%S")
                    }

                    # C. 尝试发送给对方 (如果在线)
                    is_online = await ws_manager.send_personal_message(payload, target_id)

                    if not is_online:
                        print(f"用户 {target_id} 不在线，消息已存库")

    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)
    except Exception as e:
        print(f"WS Error: {e}")
        ws_manager.disconnect(user_id)