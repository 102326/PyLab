# PyLabFastAPI/app/utils/llm_factory.py
import os
import logging
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
# 👇 [核心修改] V3 版本必须从 .langchain 导入 CallbackHandler
from langfuse.langchain import CallbackHandler
from app.config import settings

# 👇👇👇 [新增] 开启 Langfuse 调试模式，让它把报错吐出来
os.environ["LANGFUSE_DEBUG"] = "True"
logging.getLogger("langfuse").setLevel(logging.DEBUG)
class LLMFactory:
    """
    LangChain 模型工厂：统一生产带 LangFuse 监控的 LLM 实例
    """

    @staticmethod
    def get_langfuse_handler():
        """获取 LangFuse 回调处理器"""
        # 只有当配置了 Key 时才启用，防止报错
        if os.getenv("LANGFUSE_SECRET_KEY") and os.getenv("LANGFUSE_PUBLIC_KEY"):
            return [CallbackHandler(
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                host=os.getenv("LANGFUSE_HOST")
            )]
        return []

    @staticmethod
    def get_llm(temperature=0.7):
        """
        自动判断使用 DeepSeek (在线) 还是 Ollama (本地)
        """
        api_key = getattr(settings, "DEEPSEEK_API_KEY", "")
        callbacks = LLMFactory.get_langfuse_handler()

        # === 方案 A: DeepSeek 在线 API (走 OpenAI 协议) ===
        if api_key:
            return ChatOpenAI(
                model="deepseek-chat",  # 或 deepseek-reasoner (R1)
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