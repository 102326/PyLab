# PyLabFastAPI/app/views/ai.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from app.models.user import User
from app.models.chat import AIChatRecord  # 👈 引入新模型
from app.deps import get_current_user  # 👈 引入鉴权依赖
from app.workflows.rag import rag_app

router = APIRouter(prefix="/ai", tags=["AI"])


class ChatReq(BaseModel):
    question: str


# 响应模型 (用于历史记录列表)
class HistoryItem(BaseModel):
    id: int
    question: str
    answer: str
    created_at: str

    class Config:
        from_attributes = True


# 1. 聊天接口
@router.post("/chat", summary="RAG 智能问答 (带记忆存储)")
async def chat_with_ai(
        req: ChatReq,
        user: User = Depends(get_current_user)  # 👈 恢复鉴权，知道是谁在问
):
    try:
        # 1. 调用 AI (LangGraph)
        result = await rag_app.ainvoke({"question": req.question})

        answer_text = result["answer"]
        context_text = result["context"]

        # 2. [核心] 存入数据库
        await AIChatRecord.create(
            user=user,
            question=req.question,
            answer=answer_text,
            sources=context_text[:500] + "..."  # 只存前500字摘要，省空间
        )

        return {
            "code": 200,
            "msg": "回答成功",
            "data": {
                "answer": answer_text,
                "context_preview": context_text[:200] + "..."
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "msg": "AI 思考出错了，请检查后台日志",
            "data": None
        }


# 2. [新增] 获取我的历史记录接口
@router.get("/history", summary="获取 AI 历史问答")
async def get_ai_history(
        user: User = Depends(get_current_user),
        limit: int = 50
):
    # 查询当前用户的记录，按时间倒序
    records = await AIChatRecord.filter(user=user).limit(limit)

    # 转换为简单的列表返回
    data = [
        {
            "id": r.id,
            "question": r.question,
            "answer": r.answer,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for r in records
    ]

    return {
        "code": 200,
        "msg": "获取成功",
        "data": data
    }