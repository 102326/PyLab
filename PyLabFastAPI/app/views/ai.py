# PyLabFastAPI/app/views/ai.py
from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.deps import get_current_user
from app.models.user import User
from app.core.agent import PyLabAgent
from app.services.chat_service import ChatService

router = APIRouter(prefix="/ai", tags=["AI Agent"])


# --- Schemas ---
class SessionCreate(BaseModel):
    title: str = "新对话"


class SessionOut(BaseModel):
    id: UUID
    title: str
    updated_at: str  # 简化处理，实际可以使用 datetime


class ChatReq(BaseModel):
    message: str


# --- Endpoints ---

@router.get("/sessions", summary="获取会话列表")
async def list_sessions(user: User = Depends(get_current_user)):
    sessions = await ChatService.get_user_sessions(user)
    # 简单转换一下格式
    return [
        {"id": s.id, "title": s.title, "updated_at": s.updated_at.strftime("%Y-%m-%d %H:%M")}
        for s in sessions
    ]


@router.post("/sessions", summary="新建会话")
async def create_session(data: SessionCreate, user: User = Depends(get_current_user)):
    s = await ChatService.create_session(user, data.title)
    return {"id": s.id, "title": s.title}


@router.delete("/sessions/{session_id}", summary="删除会话")
async def delete_session(session_id: UUID, user: User = Depends(get_current_user)):
    await ChatService.clear_session(session_id, user)
    return {"ok": True}


@router.get("/sessions/{session_id}/history", summary="获取历史记录")
async def get_history(session_id: UUID, user: User = Depends(get_current_user)):
    # 获取历史记录用于前端回显
    return await ChatService.get_history(session_id)


@router.post("/chat/{session_id}", summary="发送消息 (流式 + 持久化)")
async def chat_stream(
        session_id: UUID,
        req: ChatReq,
        user: User = Depends(get_current_user)
):
    # 1. 保存用户消息 (Redis + DB)
    await ChatService.save_message(session_id, "user", req.message)

    # 2. 启动 Agent
    agent = PyLabAgent(user, session_id)

    async def response_generator():
        full_reply = ""
        try:
            # ⚡️ 核心：确保这里是 yield 一个个字符，而不是一整块
            async for char in agent.astream_chat(req.message):
                full_reply += char
                yield char
                # 可选：如果觉得太快，可以在这里加 await asyncio.sleep(0.01) 模拟打字机
        finally:
            if full_reply.strip():
                await ChatService.save_message(session_id, "assistant", full_reply)

    # ⚡️ 核心：强制禁用缓存 Headers
    headers = {
        "Cache-Control": "no-cache, no-transform",  # 禁止缓存和转换
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # 告诉 Nginx 别缓冲
        "Content-Type": "text/event-stream; charset=utf-8"  # 明确告诉浏览器这是流
    }

    return StreamingResponse(
        response_generator(),
        media_type="text/event-stream",  # 使用 event-stream 类型更稳
        headers=headers
    )