# PyLabFastAPI/app/services/vector_milvus.py
from pymilvus import (
    connections,
    FieldSchema, CollectionSchema, DataType,
    Collection, utility
)
from app.config import settings
import logging

logger = logging.getLogger("uvicorn")


class MilvusService:
    @classmethod
    def connect(cls):
        """建立 Milvus 连接"""
        try:
            # 检查是否已有连接，避免重复连接报错
            if utility.get_server_version():
                return
        except Exception:
            # 如果报错说明没连上，继续执行连接逻辑
            pass

        try:
            connections.connect(
                "default",
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT
            )
            logger.info(f"✅ [Milvus] Connected to {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
        except Exception as e:
            logger.error(f"❌ [Milvus] Connection failed: {e}")
            # 这里不抛出异常，防止因为向量库挂了导致整个后端无法启动(降级运行)

    @classmethod
    def init_collections(cls):
        """初始化所需的向量集合 (Schema Definition)"""
        # 1. 确保连接
        cls.connect()

        # 2. 定义 Schema 并创建集合

        # --- Collection 1: 课程元数据 (Layer 1 粗排) ---
        # 用于：根据用户 query 快速找到相关的课程
        cls._create_collection_if_not_exist(
            name=settings.MILVUS_COLLECTION_COURSE,
            fields=[
                # 课程ID作为主键，不自动生成
                FieldSchema(name="course_id", dtype=DataType.INT64, is_primary=True, auto_id=False,
                            description="课程ID"),
                # 向量维度: 假设使用 m3e-base (768维)。如果是 OpenAI (1536维) 请自行修改
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
                # 存一些关键元数据(如 JSON 字符串)，避免每次都要回 PG 查详情
                FieldSchema(name="meta_info", dtype=DataType.VARCHAR, max_length=4096)
            ],
            desc="课程元数据向量库"
        )

        # --- Collection 2: 知识点切片 (Layer 2 精排) ---
        # 用于：在特定课程或视频中，精确定位知识点
        cls._create_collection_if_not_exist(
            name=settings.MILVUS_COLLECTION_KNOWLEDGE,
            fields=[
                # 切片ID，自动生成
                FieldSchema(name="chunk_id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="course_id", dtype=DataType.INT64),  # 关联课程
                FieldSchema(name="video_id", dtype=DataType.INT64),  # 关联视频
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),  # 同上
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=8192),  # 切片文本内容
                FieldSchema(name="start_time", dtype=DataType.INT64, description="视频跳转秒数")
            ],
            desc="课程详细内容切片库"
        )

    @staticmethod
    def _create_collection_if_not_exist(name, fields, desc):
        """创建集合的通用辅助方法"""
        try:
            if utility.has_collection(name):
                logger.info(f"✅ [Milvus] Collection '{name}' exists.")
                return

            logger.info(f"🔨 [Milvus] Creating collection '{name}'...")
            schema = CollectionSchema(fields, desc)
            collection = Collection(name, schema)

            # 创建索引 (IVF_FLAT 兼顾速度和召回率)
            # nlist: 聚类中心数，根据数据量调整，128 适合中小规模
            index_params = {
                "metric_type": "COSINE",  # 余弦相似度
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            collection.create_index(field_name="embedding", index_params=index_params)

            # 加载到内存，否则无法搜索
            collection.load()
            logger.info(f"✅ [Milvus] Created & Loaded '{name}'")

        except Exception as e:
            logger.error(f"⚠️ [Milvus] Failed to init collection '{name}': {e}")