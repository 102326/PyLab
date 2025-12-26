from pydantic import BaseModel, Field
from typing import Optional

class UnifiedLoginReq(BaseModel):
    """设置统一登录参数"""
    login_type : str #登录类型
    #======密码登录参数=======
    phone: Optional[str] = Field(None, description="手机号 (密码登录/验证码登录时必填)")
    password : Optional[str] = None
    #======第三方登录参数=======
    auth_code: Optional[str] = None
    role: int = Field(0, description="注册角色: 0=学生, 1=老师")