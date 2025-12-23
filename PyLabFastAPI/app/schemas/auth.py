from pydantic import BaseModel
from typing import Optional

class UnifiedLoginReq(BaseModel):
    """设置统一登录参数"""
    login_type : str #登录类型
    #======密码登录参数=======
    username : Optional[str] = None
    password : Optional[str] = None
    #======第三方登录参数=======
    auth_code: Optional[str] = None