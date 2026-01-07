# PyLabFastAPI/app/workflows/rag.py
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig  # 👈 1. 引入类型，解决爆黄
# 根据你之前的测试，observe 直接从 langfuse 导入
from langfuse import observe
from app.utils.llm_factory import LLMFactory
from app.services.vector_db import VectorDBService


# === 1. 定义状态 (State) ===
class RAGState(TypedDict):
    question: str  # 用户问题
    context: str  # 检索到的上下文
    answer: str  # 最终答案


# === 2. 定义节点 (Nodes) ===

@observe(name="RAG-Retrieve")  # 👈 监控检索步骤
async def retrieve_node(state: RAGState):
    """
    检索节点：去向量数据库查资料
    """
    question = state["question"]
    try:
        # 调用之前的 VectorDBService
        results = await VectorDBService.search_similar_courses(question, limit=3)
        if not results:
            context = "（资料库中未找到相关内容）"
        else:
            context = "\n".join([f"- 《{r['title']}》: {r['desc']}" for r in results])
    except Exception as e:
        context = f"检索出错: {str(e)}"

    return {"context": context}


@observe(name="RAG-Generate")  # 👈 监控生成步骤
async def generate_node(state: RAGState):
    """
    生成节点：调用大模型回答
    """
    question = state["question"]
    context = state["context"]

    # 1. 获取 LLM
    llm = LLMFactory.get_llm(temperature=0.6)

    # 2. 获取回调 (用于统计 Token，虽然 observe 也能记，但这个对 LLM 消耗统计更准)
    callbacks = LLMFactory.get_langfuse_handler()

    # 3. 定义 Prompt
    prompt = ChatPromptTemplate.from_template("""
    你是一位专业的编程导师。请基于下方的【课程资料】回答用户的【问题】。

    【课程资料】：
    {context}

    【用户问题】：
    {question}

    要求：
    1. 逻辑清晰，适合新手。
    2. 如果资料中没有答案，请明确告知，并尝试用你的通用知识补充（但要说明这是补充知识）。
    3. 仅输出回答内容，不要输出思考过程标签。
    """)

    # 4. 构建链
    chain = prompt | llm | StrOutputParser()

    # 5. [解决爆黄] 构造标准的 RunnableConfig 对象
    run_config: RunnableConfig = {
        "callbacks": callbacks,
        "run_name": "DeepSeek-R1-Call"
    }

    # 6. 执行
    answer = await chain.ainvoke(
        {"question": question, "context": context},
        config=run_config  # 👈 现在 IDE 应该不会报错了
    )

    return {"answer": answer}


# === 3. 构建图 (Graph) ===
def build_rag_graph():
    workflow = StateGraph(RAGState)

    # 添加节点
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("generate", generate_node)

    # 定义边 (流程控制)
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()


# 单例模式
rag_app = build_rag_graph()