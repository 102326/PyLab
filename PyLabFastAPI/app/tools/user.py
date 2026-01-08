# PyLabFastAPI/app/tools/user.py
from langchain_core.tools import tool
from app.models.user import User
# 1. 引入刚才写的 RAG 工具
from app.tools.rag import search_course_knowledge


def get_user_tools(user: User):
    """
    为当前用户生成专属工具箱
    """

    @tool
    async def get_my_profile() -> str:
        """
        查询当前登录用户的个人详细信息。
        当用户问"我是谁"、"我的手机号"时使用。
        """
        role_map = {0: "学生", 1: "老师", 9: "管理员"}
        role_str = role_map.get(user.role, "未知角色")

        info = (
            f"用户ID: {user.id}\n"
            f"昵称: {user.nickname}\n"
            f"用户名: {user.username}\n"
            f"手机号: {user.phone or '未绑定'}\n"
            f"角色: {role_str}\n"
            f"注册时间: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return info

    # 2. 将 search_course_knowledge 加入返回列表
    return [get_my_profile, search_course_knowledge]