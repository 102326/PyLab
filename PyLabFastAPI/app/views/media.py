# PyLabFastAPI/app/views/media.py
from fastapi import APIRouter, Depends, HTTPException
from app.utils.qiniu_helper import get_upload_token
from app.config import settings
from app.deps import get_current_user
from app.models.user import User
from app.models.course import VideoResource
from app.schemas.media import VideoCreateReq

router = APIRouter(prefix="/media", tags=["Media"])


@router.get("/token")
async def get_qiniu_token(user: User = Depends(get_current_user)):
    """
    1. 前端请求上传凭证
    """
    token = get_upload_token()
    return {
        "code": 200,
        "msg": "获取凭证成功",
        "data": {
            "token": token,
            "domain": settings.QINIU_DOMAIN
        }
    }


@router.post("/videos")
async def create_video_resource(
        req: VideoCreateReq,
        user: User = Depends(get_current_user)
):
    """
    2. 前端上传七牛云成功后，调用此接口把数据存入数据库
    """
    # 拼接完整的播放地址
    play_url = f"{settings.QINIU_DOMAIN}/{req.file_key}"

    video = await VideoResource.create(
        title=req.title,
        file_key=req.file_key,
        play_url=play_url,
        duration=req.duration,
        status=1,  # 1=正常 (因为七牛云直传不需要我们转码，直接可用)
        uploader=user
    )

    return {"code": 200, "msg": "视频保存成功", "data": {"id": video.id}}