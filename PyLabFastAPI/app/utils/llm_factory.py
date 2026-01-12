import os
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
# [修改 1] 引入标准输出回调，替代 Langfuse
from langchain_core.callbacks import StdOutCallbackHandler
from app.config import settings
from dotenv import load_dotenv

load_dotenv(override=True)


class LLMFactory:
    """
    LangChain 模型工厂：生产带控制台监控的 LLM 实例
    """

    @staticmethod
    def get_callbacks():
        """
        获取回调处理器：目前仅使用控制台打印，方便调试 Agent 思考过程
        """
        # StdOutCallbackHandler 会把 Chain 的执行过程打印到终端
        return [StdOutCallbackHandler()]

    @staticmethod
    def get_llm(temperature=0.7):
        """
        自动判断使用 DeepSeek (在线) 还是 Ollama (本地)
        """
        api_key = os.getenv("DEEPSEEK_API_KEY") or getattr(settings, "DEEPSEEK_API_KEY", "")

        # 获取回调
        callbacks = LLMFactory.get_callbacks()

        # === 方案 A: DeepSeek 在线 API ===
        if api_key:
            return ChatOpenAI(
                model="deepseek-chat",
                openai_api_key=api_key,
                openai_api_base="https://api.deepseek.com",
                temperature=temperature,
                callbacks=callbacks,
                verbose=True
            )

        # === 方案 B: 本地 Ollama ===
        print("⚠️ 未检测到 DeepSeek Key，正在使用本地 Ollama...")
        return ChatOllama(
            model="deepseek-r1:7b",
            base_url="http://localhost:11434",
            temperature=temperature,
            callbacks=callbacks,
            verbose=True
        )