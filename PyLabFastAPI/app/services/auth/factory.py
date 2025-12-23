from typing import Dict,Type
from fastapi import HTTPException
from app.services.auth.base import BaseAuthStrategy
from app.services.auth.strategies import PasswordAuthStrategy, DingTalkAuthStrategy

class AuthFactory:
    _strategies: Dict[str, Type[BaseAuthStrategy]] = {
        "password": PasswordAuthStrategy,
        "dingtalk": DingTalkAuthStrategy,
    }
    @classmethod
    def get_strategy(cls,login_type:str)->BaseAuthStrategy:
        strategy_class = cls._strategies.get(login_type)
        if not strategy_class:
            raise HTTPException(status_code=400, detail=f"不支持的登录方式: {login_type}")
        return strategy_class()