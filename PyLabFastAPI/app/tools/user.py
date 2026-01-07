# PyLabFastAPI/app/tools/user.py
from langchain_core.tools import tool
from app.models.user import User


def get_user_tools(user: User):
    """
    【工厂函数】为当前特定用户生成专属工具箱。
    通过闭包 (Closure) 将 user 变量'锁'在函数内部，
    这样 Agent 调用工具时，无需（也无法）传递 user_id，保证了安全。
    """

    @tool
    async def get_my_profile() -> str:
        """
        查询当前登录用户的个人详细信息。
        当用户询问"我是谁"、"我的手机号是多少"、"我的角色是什么"时使用此工具。
        """
        # 这里直接使用外层传入的 user 对象，无需查库，或者根据 user.id 查库
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

    # 将来可以在这里添加更多工具，例如：
    # @tool
    # async def update_my_nickname(new_nickname: str): ...

    return [get_my_profile]