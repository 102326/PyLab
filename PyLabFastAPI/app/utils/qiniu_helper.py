# PyLabFastAPI/app/utils/qiniu_helper.py
from qiniu import Auth, put_data
from app.config import settings
import uuid
import datetime


def get_upload_token(bucket_name: str = None, expire: int = 3600):
    """生成七牛云上传凭证 (给前端直传用)"""
    q = Auth(settings.QINIU_ACCESS_KEY, settings.QINIU_SECRET_KEY)
    bucket = bucket_name or settings.QINIU_BUCKET_NAME
    policy = {
        "returnBody": '{"key":"$(key)","hash":"$(etag)","fsize":$(fsize),"bucket":"$(bucket)","name":"$(x:name)"}'
    }
    token = q.upload_token(bucket, expires=expire, policy=policy)
    return token


# === [新增] 服务端直传函数 ===
def upload_bytes_to_qiniu(file_data: bytes, filename: str = None):
    """
    后端直接接收文件流上传到七牛云
    """
    q = Auth(settings.QINIU_ACCESS_KEY, settings.QINIU_SECRET_KEY)

    # 1. 生成唯一文件名 (如果没有提供)
    if not filename:
        suffix = "bin"
    else:
        # 获取后缀名
        suffix = filename.split(".")[-1] if "." in filename else "bin"

    # key = 年/月/uuid.后缀
    key = f"{datetime.datetime.now().strftime('%Y/%m')}/{uuid.uuid4()}.{suffix}"

    # 2. 生成上传 Token
    token = q.upload_token(settings.QINIU_BUCKET_NAME, key, 3600)

    # 3. 调用 SDK 上传
    ret, info = put_data(token, key, file_data)

    if info.status_code == 200:
        # 返回完整的 URL
        return f"{settings.QINIU_DOMAIN}/{ret['key']}"
    else:
        print(f"七牛云上传失败: {info}")
        return None