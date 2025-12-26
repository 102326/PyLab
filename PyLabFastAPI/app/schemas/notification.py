from pydantic import BaseModel, HttpUrl

class PushKeys(BaseModel):
    p256dh: str
    auth: str

class PushSubscriptionSchema(BaseModel):
    endpoint: HttpUrl
    expirationTime: float | None = None
    keys: PushKeys