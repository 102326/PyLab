# PyLabFastAPI/app/core/agent.py
import logging
from uuid import UUID
from typing import AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from app.utils.llm_factory import LLMFactory
from app.models.user import User
from app.tools.user import get_user_tools
from app.services.chat_service import ChatService  # 👈 引入混合服务

logger = logging.getLogger(__name__)


class PyLabAgent:
    def __init__(self, user: User, session_id: UUID):
        self.user = user
        self.session_id = session_id
        self.llm = LLMFactory.get_llm(temperature=0.3)
        self.tools = get_user_tools(user)

        self.system_prompt = (
            f"你是一个智能编程教育助手 PyLab AI。当前用户: {self.user.nickname}。"
            "默认使用中文。请基于提供的历史上下文回答问题。"
        )

        # 这里的 checkpointer 仅用于管理单次推理过程中的状态
        # 长期记忆由 ChatService + Redis 托管
        self.graph = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=self.system_prompt,
            checkpointer=MemorySaver()
        )

    async def astream_chat(self, user_input: str) -> AsyncGenerator[str, None]:
        # 1. 获取混合存储中的历史记录 (Redis -> DB)
        history_dicts = await ChatService.get_history(self.session_id)

        # 2. 转换为 LangChain 消息格式
        langchain_msgs = []
        for msg in history_dicts:
            if msg['role'] == 'user':
                langchain_msgs.append(HumanMessage(content=msg['content']))
            elif msg['role'] in ['ai', 'assistant']:
                langchain_msgs.append(AIMessage(content=msg['content']))

        # 3. 追加当前问题
        langchain_msgs.append(HumanMessage(content=user_input))

        # 4. 执行推理
        # 注意：我们将历史直接注入 messages，LangGraph 会自动处理上下文
        inputs = {"messages": langchain_msgs}
        config = {"configurable": {"thread_id": str(self.session_id)}}

        try:
            async for event in self.graph.astream_events(inputs, config=config, version="v2"):
                if event["event"] == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        yield content
        except Exception as e:
            logger.error(f"Agent Error: {e}")
            yield f"⚠️ Error: {str(e)}"