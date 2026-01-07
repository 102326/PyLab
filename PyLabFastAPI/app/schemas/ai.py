# PyLabFastAPI/app/schemas/ai.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class AIChatRequest(BaseModel):
    """前端发送给 AI 的对话请求"""
    message: str = Field(..., description="用户的输入内容")
    history: List[Dict[str, str]] = Field(default=[], description="历史对话上下文 (OpenAI 格式: [{'role': 'user', 'content': '...'}])")

class AIResponse(BaseModel):
    """非流式返回时的结构 (流式通常直接返回字符串片段)"""
    reply: str
    tool_calls: Optional[List[Dict[str, Any]]] = None