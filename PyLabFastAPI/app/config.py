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

    # Celery 配置
    CELERY_BROKER_URL: str = "redis://127.0.0.1:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://127.0.0.1:6379/2"

    # === 七牛云配置 ===
    QINIU_ACCESS_KEY: str
    QINIU_SECRET_KEY: str
    QINIU_BUCKET_NAME: str
    QINIU_DOMAIN: str

    # === 百度云 OCR ===
    BAIDU_APP_ID: str = ""
    BAIDU_API_KEY: str = ""
    BAIDU_SECRET_KEY: str = ""

    # === AI / LLM 配置 ===
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_MODEL_NAME: str = "deepseek-chat"
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-zh-v1.5"
    ES_URL: str = "http://127.0.0.1:9200"

    # === RabbitMQ ===
    RABBITMQ_URL: str = "amqp://user:password@127.0.0.1:5672/"

    # 👇👇👇 [这里修正了] 加上了 : str 类型注解
    LANGFUSE_SECRET_KEY: str = "sk-lf-2aa47f70-cb84-454e-90b3-ac8c506780ab"
    LANGFUSE_PUBLIC_KEY: str = "pk-lf-6015c4ba-8e38-4113-8314-94e7d5915930"

    # 注意：Langfuse SDK 默认读的是 LANGFUSE_HOST，你代码里写的是 BASE_URL
    # 为了防止 SDK 读不到，建议这里还是叫 LANGFUSE_HOST
    # 或者你在 .env 里同时写上 LANGFUSE_HOST=...
    LANGFUSE_HOST: str = "http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()