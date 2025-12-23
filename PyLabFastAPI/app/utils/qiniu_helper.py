# PyLabFastAPI/app/utils/qiniu_helper.py
from qiniu import Auth
from app.config import settings


def get_upload_token(bucket_name: str = None, expire: int = 3600):
    """
    生成七牛云上传凭证
    """
    q = Auth(settings.QINIU_ACCESS_KEY, settings.QINIU_SECRET_KEY)
    bucket = bucket_name or settings.QINIU_BUCKET_NAME

    # 策略：允许前端上传后，七牛返回这些信息给前端
    # $(key) 是文件名，$(etag) 是文件指纹，$(fsize) 是文件大小
    policy = {
        "returnBody": '{"key":"$(key)","hash":"$(etag)","fsize":$(fsize),"bucket":"$(bucket)","name":"$(x:name)"}'
    }

    token = q.upload_token(bucket, expires=expire, policy=policy)
    return token