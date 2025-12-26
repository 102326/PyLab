# PyLabFastAPI/app/views/media.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.utils.qiniu_helper import get_upload_token, upload_bytes_to_qiniu # 引入新函数
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


# === [新增] 简单文件上传接口 ===
@router.post("/upload")
async def upload_file(
        file: UploadFile = File(...),
        user: User = Depends(get_current_user)
):
    """
    通用文件上传接口 (语音、图片等)
    """
    # 1. 读取文件内容
    content = await file.read()

    # 2. 上传到七牛云
    url = upload_bytes_to_qiniu(content, file.filename)

    if not url:
        raise HTTPException(status_code=500, detail="文件上传失败")

    return {
        "code": 200,
        "msg": "上传成功",
        "data": {"url": url}  # 前端拿这个 url 发给 websocket
    }