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
from app.services.chat_service import ChatService  # 👈 引入混合存储服务

logger = logging.getLogger(__name__)


class PyLabAgent:
    """
    PyLab 业务智能体 (支持持久化会话)
    """

    def __init__(self, user: User, session_id: UUID):
        self.user = user
        self.session_id = session_id  # 绑定会话
        self.llm = LLMFactory.get_llm(temperature=0.3)
        self.tools = get_user_tools(user)

        # System Prompt
        self.system_prompt = (
            f"你是一个智能编程教育助手 PyLab AI。当前用户: {self.user.nickname}。"
            "默认使用中文。请基于提供的历史上下文回答问题。"
            "严禁编造用户信息。"
        )

        # 创建 Graph
        # checkpointer=MemorySaver() 这里仅用于"单轮对话内"的多步思考状态保存
        # 跨轮次的历史记录由 astream_chat 手动注入
        self.graph = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=self.system_prompt,
            checkpointer=MemorySaver()
        )

    async def astream_chat(self, user_input: str) -> AsyncGenerator[str, None]:
        """
        全自动流程：加载历史 -> 注入上下文 -> 推理 -> 流式输出
        """
        # 1. 从 Redis/DB 获取历史记录 (List[Dict])
        # 比如: [{'role': 'user', 'content': 'hi'}, {'role': 'assistant', 'content': 'hello'}]
        history_dicts = await ChatService.get_history(self.session_id)

        # 2. 转换为 LangChain 消息对象
        langchain_msgs = []
        for msg in history_dicts:
            if msg['role'] == 'user':
                langchain_msgs.append(HumanMessage(content=msg['content']))
            elif msg['role'] in ['ai', 'assistant']:
                langchain_msgs.append(AIMessage(content=msg['content']))

        # 3. 追加当前用户的新问题
        langchain_msgs.append(HumanMessage(content=user_input))

        # 4. 构造输入
        # 注意：LangGraph 的 prebuilt agent 能够识别 messages 列表并自动处理上下文
        inputs = {"messages": langchain_msgs}

        # 这里的 thread_id 仅区分内存中的执行线程，防止并发串台
        config = {"configurable": {"thread_id": str(self.session_id)}}

        try:
            # 5. 执行推理流
            async for event in self.graph.astream_events(inputs, config=config, version="v2"):
                # 筛选 LLM 生成的文本块
                if event["event"] == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        yield content

        except Exception as e:
            logger.error(f"Agent Error: {e}")
            yield f"⚠️ 思考过程中断: {str(e)}"