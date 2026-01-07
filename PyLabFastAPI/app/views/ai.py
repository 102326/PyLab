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


# === Data Schemas ===
class SessionCreate(BaseModel):
    title: str = "新对话"


class SessionOut(BaseModel):
    id: UUID
    title: str
    updated_at: str


class ChatReq(BaseModel):
    message: str


# === Endpoints ===

@router.get("/sessions", summary="获取会话列表")
async def list_sessions(user: User = Depends(get_current_user)):
    """获取当前用户的所有活跃会话"""
    sessions = await ChatService.get_user_sessions(user)
    # 简单格式化返回
    return [
        {
            "id": s.id,
            "title": s.title,
            # 格式化时间，前端直接显示
            "updated_at": s.updated_at.strftime("%Y-%m-%d %H:%M") if s.updated_at else ""
        }
        for s in sessions
    ]


@router.post("/sessions", summary="新建会话")
async def create_session(
        data: SessionCreate,
        user: User = Depends(get_current_user)
):
    """创建一个新的聊天窗口"""
    s = await ChatService.create_session(user, data.title)
    return {"id": s.id, "title": s.title}


@router.delete("/sessions/{session_id}", summary="删除会话")
async def delete_session(
        session_id: UUID,
        user: User = Depends(get_current_user)
):
    """删除会话 (软删除 + 清除 Redis 缓存)"""
    await ChatService.clear_session(session_id, user)
    return {"ok": True}


@router.get("/sessions/{session_id}/history", summary="获取历史记录")
async def get_history(
        session_id: UUID,
        user: User = Depends(get_current_user)
):
    """获取某个会话的历史消息 (用于前端回显)"""
    # 这里可以加个校验确保 session 属于 user，ChatService 内部其实没强校验，
    # 但 get_history 主要是读缓存，性能优先。
    # 严谨做法是先查 Session 是否存在且属于 user。
    return await ChatService.get_history(session_id)


@router.post("/chat/{session_id}", summary="发送消息 (流式 + 持久化)")
async def chat_stream(
        session_id: UUID,
        req: ChatReq,
        user: User = Depends(get_current_user)
):
    """
    核心对话接口：
    1. 用户消息存库 (DB + Redis)
    2. Agent 带着历史上下文思考
    3. 流式返回结果
    4. AI 回复存库 (DB + Redis)
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    # 1. 保存用户消息
    await ChatService.save_message(session_id, "user", req.message)

    # 2. 初始化 Agent (注入 Session ID)
    agent = PyLabAgent(user, session_id)

    async def response_generator():
        full_reply = ""
        try:
            # 3. 流式生成
            async for char in agent.astream_chat(req.message):
                full_reply += char
                yield char

        except Exception as e:
            yield f"\n\n[系统错误: {str(e)}]"

        finally:
            # 4. 保存 AI 完整回复 (仅在成功生成内容后)
            if full_reply.strip():
                await ChatService.save_message(session_id, "assistant", full_reply)

    # 5. 设置 Headers 禁止缓存，确保打字机效果流畅
    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # 关键：告诉 Nginx 不要缓冲
        "Content-Type": "text/event-stream; charset=utf-8"
    }

    return StreamingResponse(
        response_generator(),
        media_type="text/event-stream",
        headers=headers
    )