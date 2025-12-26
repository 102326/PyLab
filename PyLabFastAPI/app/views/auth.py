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
from app.tasks.ocr_tasks import verify_idcard_task
router = APIRouter(prefix="/auth", tags=["Auth"])


# === 统一登录接口 (工厂模式入口) ===
@router.post("/login")
async def unified_login(req: UnifiedLoginReq):
    # 注意：现在的登录策略可能还是在用 username 查库
    # 如果你的 AuthStrategy 里是用 username=req.username 查的
    # 那么注册时必须保证 username 里有值（可以是手机号）

    # 暂时保持现有逻辑，后续如果要分离 username/phone 登录，需修改 strategy
    strategy = AuthFactory.get_strategy(req.login_type)

    # 这里我们假设前端传来的 phone 在 req.username 字段里 (因为 UnifiedLoginReq 的定义)
    # 或者前端改了模型传 phone，这里要做适配
    # 假设前端传的是：{ "login_type": "password", "phone": "138...", "password": "..." }
    # Pydantic 会把 phone 映射到 UnifiedLoginReq 的对应字段

    user = await strategy.authenticate(req)
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
                "avatar": user.avatar,
                "role": user.role
            }
        }
    }


# === 核心修复：注册接口 ===
@router.post("/register")
async def register(req: UnifiedLoginReq):
    if req.login_type != "password":
        raise HTTPException(status_code=400, detail="目前只支持账号密码注册")

    # 前端传来的手机号字段是 phone
    phone_number = req.phone

    if not phone_number:
        raise HTTPException(status_code=400, detail="手机号不能为空")

    # 1. 检查手机号是否已存在 (查 phone 字段)
    if await User.filter(phone=phone_number).exists():
        raise HTTPException(status_code=400, detail="该手机号已注册")

    # 2. 创建用户
    # 逻辑修正：
    # username -> 存手机号 (作为登录账号)
    # phone    -> 存手机号 (作为联系方式)
    # 这样既保证了能用 username 登录 (兼容旧逻辑)，也正确填充了 phone 字段
    await User.create(
        username=phone_number,  # <--- 登录账号 = 手机号
        phone=phone_number,  # <--- 手机号字段 = 手机号
        password=get_password_hash(req.password),
        nickname=f"用户{phone_number[-4:]}",
        role=req.role
    )

    return {"code": 200, "msg": "注册成功"}


# 定义请求参数
class IDCardVerifyReq(BaseModel):
    front_url: str
    back_url: str


@router.post("/verify/idcard")
async def verify_idcard(
        req: IDCardVerifyReq,
        user: User = Depends(get_current_user)
):
    if user.role == UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="管理员无需认证")

    profile = await TeacherProfile.get_or_none(user=user)
    if profile and profile.verify_status == 2:
        raise HTTPException(status_code=400, detail="您已通过实名认证")

    if not profile:
        profile = await TeacherProfile.create(user=user)

    profile.verify_status = 1
    profile.id_card_img_f = req.front_url
    profile.id_card_img_b = req.back_url
    await profile.save()

    verify_idcard_task.delay(user.id, req.front_url, req.back_url)

    return {
        "code": 200,
        "msg": "提交成功，系统正在后台审核",
        "data": {"status": 1}
    }


@router.get("/me")
async def get_my_info(user: User = Depends(get_current_user)):
    teacher_profile = await TeacherProfile.get_or_none(user=user)
    return {
        "code": 200,
        "msg": "获取成功",
        "data": {
            "user_info": {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "avatar": user.avatar,
                "role": user.role,
                "phone": user.phone  # 可以顺便把 phone 也返回回去
            },
            "teacher_profile": teacher_profile
        }
    }