from fastapi import HTTPException
import uuid
from passlib.exc import UnknownHashError
from app.models.user import User, SocialAccount
from app.schemas.auth import UnifiedLoginReq
from app.services.auth.base import BaseAuthStrategy
from app.utils.dingtalk import DingTalkHelper
from app.utils.security import verify_password


#===账号密码登录策略===
class PasswordAuthStrategy(BaseAuthStrategy):
    """手机号密码登录策略"""
    async def authenticate(self, req: UnifiedLoginReq) -> User:
        # 1. 校验参数
        if not req.phone or not req.password:
            raise HTTPException(status_code=400, detail="手机号和密码不能为空")

        # 2. 查找用户 (核心修改：username -> phone)
        # 注意：这里改成了用 phone 查找
        user = await User.filter(phone=req.phone).first()

        # 3. 验证用户和密码
        if not user:
            # 为了安全，不要提示“用户不存在”，而是提示模糊信息
            raise HTTPException(status_code=400, detail="手机号或密码错误")

        if not user.password:
            raise HTTPException(status_code=400, detail="该账号未设置密码，请使用验证码登录")

        if not verify_password(req.password, user.password):
            raise HTTPException(status_code=400, detail="手机号或密码错误")

        # 4. 检查账号状态
        if not user.is_active:
            raise HTTPException(status_code=400, detail="账号已被禁用")

        return user

#===钉钉登录策略===
class DingTalkAuthStrategy(BaseAuthStrategy):
    async def authenticate(self, req: UnifiedLoginReq) -> User:
        # 1. 校验参数
        if not req.auth_code:
            raise HTTPException(status_code=400, detail="缺少auth_code")

        # 2. 调用工具类获取钉钉用户信息
        user_info, error = await DingTalkHelper.get_user_info_by_code(req.auth_code)
        if error:
            raise HTTPException(status_code=400, detail=f"钉钉登录失败: {error}")

        # 3. 确定第三方唯一标识
        dingtalk_id = user_info.get("unionid") or user_info.get("openid")
        if not dingtalk_id:
            raise HTTPException(status_code=400, detail="无法获取有效的钉钉用户标识")

        # === 核心逻辑重构：不再提前 return ===

        user = None

        # A. 第一层查找：尝试通过 SocialAccount 找人
        social_account = await SocialAccount.filter(
            platform="dingtalk",
            openid=dingtalk_id
        ).prefetch_related("user").first()

        if social_account:
            user = social_account.user

        # B. 第二层查找：如果没找到，尝试通过手机号“捞”人 (账号合并)
        if not user:
            phone = user_info.get("phone")
            if phone:
                user = await User.filter(phone=phone).first()
                if user:
                    print(f"检测到已存在手机号 {phone} 的用户，进行账号绑定...")

                    # 既然找到了老用户，顺手把绑定关系建好
                    await SocialAccount.create(
                        user=user,
                        platform="dingtalk",
                        openid=dingtalk_id,
                        union_info=user_info
                    )

        # C. 第三层：如果还是没人，说明是纯新用户，注册之
        if not user:
            new_username = f"dd_{uuid.uuid4().hex[:8]}"
            user = await User.create(
                username=new_username,
                # 这里先填钉钉的信息，如果钉钉没名也没头，就留空
                nickname=user_info.get("nick", "钉钉用户"),
                avatar=user_info.get("avatar", ""),
                phone=user_info.get("phone"),
                password=None
            )
            # 创建绑定
            await SocialAccount.create(
                user=user,
                platform="dingtalk",
                openid=dingtalk_id,
                union_info=user_info
            )

        # === D. 统一补全逻辑 (Enrichment) ===
        # 无论你是步骤A的老用户，还是步骤B的合并用户，还是步骤C的新用户
        # 只要代码走到这里，user 变量一定有值。我们在这里统一检查是否需要补全信息。

        need_save = False

        # 1. 补全昵称 (仅当数据库为空时)
        if not user.nickname and user_info.get("nick"):
            user.nickname = user_info.get("nick")
            need_save = True

        # 2. 补全头像 (仅当数据库为空时)
        if not user.avatar and user_info.get("avatar"):
            user.avatar = user_info.get("avatar")
            need_save = True

        # 3. 如果有改动，统一保存
        if need_save:
            await user.save()
            print(f"用户 {user.username} 的基础信息已通过钉钉自动补全")

        return user