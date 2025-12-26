# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # === 钉钉配置 ===
    DINGTALK_APPID: str
    DINGTALK_APPSECRET: str

    # === JWT 配置 ===
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # === 数据库配置 ===
    REDIS_URL: str
    DB_URL: str
    # Broker: 任务队列使用 Redis DB 1
    CELERY_BROKER_URL: str = "redis://127.0.0.1:6379/1"
    # Backend: 结果存储使用 Redis DB 2
    CELERY_RESULT_BACKEND: str = "redis://127.0.0.1:6379/2"

    # === 七牛云配置 ===
    QINIU_ACCESS_KEY: str
    QINIU_SECRET_KEY: str
    QINIU_BUCKET_NAME: str
    QINIU_DOMAIN: str

    # === 百度云 OCR 配置 (新增) ===
    # 允许为空(Optional)，或者给默认值 None，防止没填报错
    BAIDU_APP_ID: str = ""
    BAIDU_API_KEY: str = ""
    BAIDU_SECRET_KEY: str = ""

    # === [核心新增] AI / LLM 配置 (DeepSeek / OpenAI) ===
    # 默认指向 DeepSeek 官方 API 地址
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.deepseek.com/v1"

    # 聊天模型 (用于生成回答)
    LLM_MODEL_NAME: str = "deepseek-chat"

    # 向量模型 (用于本地 HuggingFace)
    # 推荐使用 BAAI/bge-small-zh-v1.5 (小巧强悍) 或 BAAI/bge-m3 (全能)
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-zh-v1.5"

    # === 核心配置：加载 .env 文件 ===
    model_config = SettingsConfigDict(
        env_file=".env",  # 指定读取的文件名
        env_file_encoding="utf-8",
        extra="ignore"  # 忽略 .env 中多余的字段
    )

settings = Settings()




