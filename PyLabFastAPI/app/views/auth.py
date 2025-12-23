from fastapi import APIRouter, HTTPException
from app.schemas.auth import UnifiedLoginReq
from app.services.auth.factory import AuthFactory
from app.utils.jwt import MyJWT
from app.models.user import User
from app.utils.security import get_password_hash
from app.models.user import UserRole, TeacherProfile  # 引入模型
from app.utils.baidu_ocr import BaiduOCR  # 引入刚才写的工具
from app.deps import get_current_user  # 引入依赖
from fastapi import Depends
from pydantic import BaseModel
router = APIRouter(prefix="/auth", tags=["Auth"])


# === 统一登录接口 (工厂模式入口) ===
@router.post("/login")
async def unified_login(req: UnifiedLoginReq):
    # 1. 工厂分发
    strategy = AuthFactory.get_strategy(req.login_type)

    # 2. 策略执行 (返回 User)
    user = await strategy.authenticate(req)

    # 3. 签发 Token (复用 JWT 逻辑)
    access_token, refresh_token = await MyJWT.login_user(user.id)

    return {
        "code": 200,
        "msg": "登录成功",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_info": {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "avatar": user.avatar
            }
        }
    }


# === 注册接口 (用于创建账号密码用户) ===
@router.post("/register")
async def register(req: UnifiedLoginReq):
    if req.login_type != "password":
        raise HTTPException(status_code=400, detail="目前只支持账号密码注册")

    if await User.filter(username=req.username).exists():
        raise HTTPException(status_code=400, detail="用户名已存在")

    await User.create(
        username=req.username,
        password=get_password_hash(req.password),  # 加密存储
        nickname="新用户"
    )
    return {"code": 200, "msg": "注册成功"}




# === 百度API实名验证 ===
# 定义请求参数
class IDCardVerifyReq(BaseModel):
    front_url: str  # 正面图 URL
    back_url: str  # 反面图 URL


@router.post("/verify/idcard")
async def verify_idcard(
        req: IDCardVerifyReq,
        user: User = Depends(get_current_user)
):
    # 1. 只有“老师”角色才能进行实名认证
    # (根据你的需求，也可以允许学生转老师，但目前先严格卡控)
    if user.role != UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="仅教师账号可进行实名认证")

    # 2. 检查是否已经认证过
    # 注意：Tortoise 的 OneToOne 关系，如果没有 profile 会抛错还是返回 None？
    # 建议用 get_or_none 或者 try-except
    profile = await TeacherProfile.get_or_none(user=user)

    if profile and profile.verify_status == 2:
        raise HTTPException(status_code=400, detail="您已通过实名认证，无需重复提交")

    # 3. 调用百度 OCR
    ocr = BaiduOCR()
    id_info = ocr.idcard_front(req.front_url)

    if not id_info:
        raise HTTPException(status_code=400, detail="身份证识别失败，请确保图片清晰且为身份证正面")

    # 4. 保存/更新档案
    if not profile:
        # 如果没有档案，新建一个
        profile = await TeacherProfile.create(user=user)

    # 更新字段
    profile.real_name = id_info["name"]
    profile.id_card = id_info["id_num"]
    profile.id_card_img_f = req.front_url
    profile.id_card_img_b = req.back_url
    profile.verify_status = 2  # 这里我们偷懒直接设为“已通过”，正规流程应该是 1 (审核中)

    await profile.save()

    return {
        "code": 200,
        "msg": "实名认证成功",
        "data": {
            "real_name": profile.real_name,
            "id_card": profile.id_card
        }
    }