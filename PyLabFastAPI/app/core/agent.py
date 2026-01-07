# PyLabFastAPI/app/core/agent.py
import logging
from typing import AsyncGenerator, List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from app.utils.llm_factory import LLMFactory
from app.models.user import User
from app.tools.user import get_user_tools

logger = logging.getLogger(__name__)


class PyLabAgent:
    """
    PyLab 业务智能体 (基于 LangGraph v1.0.5+)
    """

    def __init__(self, user: User):
        self.user = user
        self.thread_id = str(user.id)  # 使用用户ID作为线程ID

        # 1. 获取 LLM
        self.llm = LLMFactory.get_llm(temperature=0.3)

        # 2. 获取工具链
        self.tools = get_user_tools(user)

        # 3. 构建 System Prompt
        self.system_prompt = (
            f"你是一个智能编程教育助手 PyLab AI。当前对话的用户是 {self.user.nickname} (ID: {self.user.role})。"
            "请默认使用中文回答。"
            "你可以使用工具查询数据，但严禁编造用户信息。"
            "如果用户询问与编程、课程无关的问题，请礼貌拒绝。"
        )

        # 4. 创建 Graph
        # 【核心修复】将 state_modifier 改为 prompt
        self.graph = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=self.system_prompt,  # 👈 这里改成了 prompt
            checkpointer=MemorySaver()
        )

    async def astream_chat(self, user_input: str, history: List[dict] = None) -> AsyncGenerator[str, None]:
        """
        流式对话接口
        """
        config = {"configurable": {"thread_id": self.thread_id}}

        # LangGraph 会自动管理历史，这里只传最新消息
        inputs = {"messages": [HumanMessage(content=user_input)]}

        try:
            # v2 版本流式输出
            async for event in self.graph.astream_events(inputs, config=config, version="v2"):
                kind = event["event"]

                # 过滤出 LLM 生成的文本块
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        yield content

        except Exception as e:
            logger.error(f"Agent Error: {e}")
            # 发生错误时，返回友好的提示（这在流式接口中很重要，防止前端断连）
            yield f"⚠️ 抱歉，AI 遇到了一点小问题: {str(e)}"