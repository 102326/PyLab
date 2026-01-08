# PyLabFastAPI/app/tools/rag.py
from langchain_core.tools import tool
from app.services.vector_db import VectorDBService


@tool
async def search_course_knowledge(query: str) -> str:
    """
    【核心工具】当用户询问具体课程内容、编程知识点（如 "Python装饰器"、"Vue组件"）、
    或者询问平台有哪些课程时，必须调用此工具进行搜索。

    Args:
        query: 用户的搜索关键词 (例如: "Python入门", "Java 多线程")

    Returns:
        相关的课程标题和简介摘要
    """
    print(f"🔍 [Agent] 正在调用 RAG 工具搜索: {query}")

    try:
        # 调用你现有的向量搜索服务
        # limit=3 足够了，给 LLM 太多上下文会晕
        results = await VectorDBService.search_similar_courses(query, limit=3, threshold=0.4)

        if not results:
            return "📭 知识库搜索结果为空，请尝试更换关键词。"

        # 将结构化数据格式化为 LLM 易读的文本
        context_str = "【检索到的课程资料】:\n"
        for i, item in enumerate(results, 1):
            # 过滤掉 None 的字段
            title = item.get('title', '未知标题')
            desc = item.get('desc', '暂无简介')
            # 截断过长的简介，节省 Token
            desc_short = desc[:150] + "..." if desc and len(desc) > 150 else desc

            context_str += f"{i}. 《{title}》\n   简介: {desc_short}\n"

        return context_str

    except Exception as e:
        return f"⚠️ 搜索过程中发生系统错误: {str(e)}"