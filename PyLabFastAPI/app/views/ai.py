# PyLabFastAPI/app/views/ai.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.models.user import User
from app.deps import get_current_user
from app.workflows.rag import rag_app  # 👈 引入刚才写的 Graph

router = APIRouter(prefix="/ai", tags=["AI"])


class ChatReq(BaseModel):
    question: str


@router.post("/chat", summary="RAG 智能问答 (LangGraph版)")
async def chat_with_ai(req: ChatReq):
    # 运行 LangGraph
    # ainvoke 输入是初始状态，返回是最终状态
    try:
        result = await rag_app.ainvoke({"question": req.question})

        # LangFuse 会自动在后台记录整个 Trace

        return {
            "code": 200,
            "msg": "回答成功",
            "data": {
                "answer": result["answer"],
                "context_preview": result["context"][:200] + "..."  # 给前端看一眼参考了啥
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