# PyLabFastAPI/app/schemas/media.py
from pydantic import BaseModel

class VideoCreateReq(BaseModel):
    title: str          # 视频标题
    file_key: str       # 七牛云返回的文件 Key
    file_hash: str      # 文件指纹 (etag)
    file_size: int      # 文件大小
    duration: int = 0   # 视频时长 (秒)