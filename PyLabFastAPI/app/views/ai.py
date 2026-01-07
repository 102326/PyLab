# PyLabFastAPI/app/views/ai.py
from fastapi import APIRouter, Depends, Body
from fastapi.responses import StreamingResponse
from app.deps import get_current_user
from app.models.user import User
from app.schemas.ai import AIChatRequest
from app.core.agent import PyLabAgent

router = APIRouter(prefix="/ai", tags=["AI Agent"])

@router.post("/chat", summary="AI 智能对话 (流式)")
async def ai_chat(
    req: AIChatRequest,
    user: User = Depends(get_current_user)
):
    """
    与 AI Agent 对话。
    Agent 会自动根据当前用户身份加载对应工具（如查询个人信息）。
    """
    # 1. 初始化 Agent
    agent = PyLabAgent(user)

    # 2. 定义流生成器
    async def response_generator():
        try:
            async for text in agent.astream_chat(req.message, req.history):
                # SSE 格式或者直接文本流，这里为了简单直接推文本
                # 前端 fetch 读取 body.getReader() 即可
                yield text
        except Exception as e:
            yield f"⚠️ AI 思考过程中发生错误: {str(e)}"

    # 3. 返回流式响应
    return StreamingResponse(
        response_generator(),
        media_type="text/plain" # 或者 text/event-stream
    )