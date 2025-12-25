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





# 定义请求参数
class IDCardVerifyReq(BaseModel):
    front_url: str
    back_url: str


@router.post("/verify/idcard")
async def verify_idcard(
        req: IDCardVerifyReq,
        user: User = Depends(get_current_user)
):
    # 1. 权限校验
    if user.role != UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="仅教师账号可进行实名认证")

    # 2. 检查当前状态
    profile = await TeacherProfile.get_or_none(user=user)

    # 如果已经通过，拦截
    if profile and profile.verify_status == 2:
        raise HTTPException(status_code=400, detail="您已通过实名认证")

    # 如果没有档案，先创建
    if not profile:
        profile = await TeacherProfile.create(user=user)

    # 3. [关键] 先将状态置为 "1 (审核中)" 并存库
    # 这样用户在前端立刻就能看到“审核中”的状态
    profile.verify_status = 1
    profile.id_card_img_f = req.front_url
    profile.id_card_img_b = req.back_url
    await profile.save()

    # 4. [关键] 生产者发布任务
    # .delay() 会把消息扔进 Redis，耗时极短
    verify_idcard_task.delay(user.id, req.front_url, req.back_url)

    # 5. 立即响应前端
    return {
        "code": 200,
        "msg": "提交成功，系统正在后台审核",
        "data": {
            "status": 1,  # 告诉前端现在的状态
            "tips": "预计 3 秒内完成，请稍后刷新查看"
        }
    }


@router.get("/me")
async def get_my_info(user: User = Depends(get_current_user)):
    """
    获取当前登录用户的完整信息，包括教师档案状态
    """
    # 查询关联的教师档案
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
                "role": user.role
            },
            # 将档案信息也返回给前端
            "teacher_profile": teacher_profile
        }
    }