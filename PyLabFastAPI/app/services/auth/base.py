from abc import ABC,abstractmethod
from app.models.user import User
from app.schemas.auth import UnifiedLoginReq

class BaseAuthStrategy(ABC):
    """设定抽象接口(认证策略基类)"""
    @abstractmethod
    async def authenticate(self, req: UnifiedLoginReq) -> User:
        """设定抽象方法"""
        pass
