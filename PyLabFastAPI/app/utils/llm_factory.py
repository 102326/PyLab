# PyLabFastAPI/app/utils/llm_factory.py
import os
import logging
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langfuse.langchain import CallbackHandler
from app.config import settings
from dotenv import load_dotenv

# 确保环境变量被加载 (虽然 main.py 加载过，这里再加载一次双重保险)
load_dotenv(override=True)

# 开启调试日志
# os.environ["LANGFUSE_DEBUG"] = "True"
# logging.getLogger("langfuse").setLevel(logging.DEBUG)


class LLMFactory:
    """
    LangChain 模型工厂：统一生产带 LangFuse 监控的 LLM 实例
    """

    @staticmethod
    def get_langfuse_handler():
        """获取 LangFuse 回调处理器"""
        # 只要环境变量里有 Key，就创建一个空的 Handler
        # V3 版本会自动读取 os.environ 中的 LANGFUSE_... 变量
        if os.getenv("LANGFUSE_SECRET_KEY") and os.getenv("LANGFUSE_PUBLIC_KEY"):
            return [CallbackHandler()]
        return []

    @staticmethod
    def get_llm(temperature=0.7):
        """
        自动判断使用 DeepSeek (在线) 还是 Ollama (本地)
        """
        # 优先从 .env 读取 Key，读不到再从 settings 读
        api_key = os.getenv("DEEPSEEK_API_KEY") or getattr(settings, "DEEPSEEK_API_KEY", "")

        # 获取回调 (此时是干净的 Handler)
        callbacks = LLMFactory.get_langfuse_handler()

        # === 方案 A: DeepSeek 在线 API (走 OpenAI 协议) ===
        if api_key:
            return ChatOpenAI(
                model="deepseek-chat",
                openai_api_key=api_key,
                openai_api_base="https://api.deepseek.com",
                temperature=temperature,
                callbacks=callbacks,  # 初始化时绑定一次
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