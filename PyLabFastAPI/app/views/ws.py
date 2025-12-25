# app/views/ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.core.socket_manager import ws_manager

router = APIRouter()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    # 这里可以加上 JWT Token 校验逻辑
    # token = websocket.query_params.get("token") ...

    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            # 保持连接活跃，也可以接收前端的心跳包
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)