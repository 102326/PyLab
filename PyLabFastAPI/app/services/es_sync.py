# app/services/es_sync.py
from datetime import datetime
from app.core.es import ESClient
from app.models.course import Course


class CourseESService:
    INDEX_NAME = "pylab_courses"

    @classmethod
    async def create_index(cls):
        """创建索引映射 (Mapping)"""
        client = ESClient.get()
        # 检查索引是否存在
        exists = await client.indices.exists(index=cls.INDEX_NAME)
        if not exists:
            # 定义 Mapping: 使用 ik_max_word 做细粒度分词
            mapping = {
                "properties": {
                    "id": {"type": "integer"},
                    "title": {
                        "type": "text",
                        "analyzer": "ik_max_word",
                        "search_analyzer": "ik_smart"
                    },
                    "desc": {
                        "type": "text",
                        "analyzer": "ik_max_word",
                        "search_analyzer": "ik_smart"
                    },
                    "price": {"type": "float"},
                    "is_published": {"type": "boolean"},
                    "created_at": {"type": "date"}
                }
            }
            await client.indices.create(index=cls.INDEX_NAME, mappings=mapping)
            print(f"✅ [ES] 索引 {cls.INDEX_NAME} 创建成功")

    @classmethod
    async def sync_course(cls, course: Course):
        """同步单个课程到 ES"""
        client = ESClient.get()

        # 构造文档
        doc = {
            "id": course.id,
            "title": course.title,
            "desc": course.desc or "",
            "price": float(course.price) if course.price else 0.0,
            "is_published": course.is_published,
            # 处理时间格式
            "created_at": course.created_at.isoformat() if course.created_at else datetime.now().isoformat()
        }

        # Upsert: 存在则更新，不存在则写入
        await client.index(index=cls.INDEX_NAME, id=str(course.id), document=doc)
        print(f"📡 [ES Sync] 已同步课程: {course.title}")

    @classmethod
    async def delete_course(cls, course_id: int):
        """从 ES 删除"""
        client = ESClient.get()
        await client.delete(index=cls.INDEX_NAME, id=str(course_id), ignore=[404])
        print(f"🗑️ [ES Sync] 已删除课程 ID: {course_id}")

    @classmethod
    async def search(cls, keyword: str):
        """混合搜索 (暂时只演示关键词)"""
        client = ESClient.get()

        query = {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": keyword,
                            # 标题权重 x3，描述权重 x1
                            "fields": ["title^3", "desc"],
                            "type": "best_fields"
                        }
                    }
                ],
                "filter": [
                    {"term": {"is_published": True}}
                ]
            }
        }

        resp = await client.search(index=cls.INDEX_NAME, query=query)
        # 提取 _source
        return [h["_source"] for h in resp["hits"]["hits"]]