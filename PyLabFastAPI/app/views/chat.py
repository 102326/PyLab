# PyLabFastAPI/app/views/chat.py
from fastapi import APIRouter, Depends
from app.deps import get_current_user
from app.models.user import User
# 1. 引入 PrivateMessage
from app.models.chat import PrivateMessage
from tortoise.expressions import Q
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/chat", tags=["Chat"])

class ContactSchema(BaseModel):
    id: int
    nickname: str
    avatar: Optional[str] = None
    role: int
    last_msg: Optional[str] = None
    last_time: Optional[str] = None
    unread_count: int = 0

@router.get("/contacts")
async def get_recent_contacts(user: User = Depends(get_current_user)):
    """
    获取最近联系人列表 (基于 PrivateMessage)
    """
    # 2. 修改查询模型为 PrivateMessage
    sent_to_ids = await PrivateMessage.filter(sender_id=user.id) \
        .order_by("receiver_id") \
        .distinct() \
        .values_list('receiver_id', flat=True)

    received_from_ids = await PrivateMessage.filter(receiver_id=user.id) \
        .order_by("sender_id") \
        .distinct() \
        .values_list('sender_id', flat=True)

    contact_user_ids = set(sent_to_ids + received_from_ids)
    contacts_data = []

    if contact_user_ids:
        contacts = await User.filter(id__in=contact_user_ids).all()

        for contact in contacts:
            # 3. 查最后一条私信
            last_message = await PrivateMessage.filter(
                Q(sender_id=user.id, receiver_id=contact.id) |
                Q(sender_id=contact.id, receiver_id=user.id)
            ).order_by('-created_at').first()

            # 4. 查未读数
            unread_count = await PrivateMessage.filter(
                sender_id=contact.id,
                receiver_id=user.id,
                is_read=False
            ).count()

            contacts_data.append({
                "id": contact.id,
                "nickname": contact.nickname,
                "avatar": contact.avatar,
                "role": contact.role,
                "last_msg": last_message.content if last_message else None,
                "last_time": last_message.created_at.strftime("%H:%M") if last_message else None,
                "unread_count": unread_count
            })

    # 冷启动推荐
    if not contacts_data and user.role == 0:
        teachers = await User.filter(role=1).limit(5)
        for t in teachers:
            contacts_data.append({
                "id": t.id,
                "nickname": f"{t.nickname} (推荐)",
                "avatar": t.avatar,
                "role": t.role,
                "last_msg": "你好，我是老师，有问题可以问我",
                "last_time": "",
                "unread_count": 0
            })

    contacts_data.sort(key=lambda x: x['last_time'] or "", reverse=True)
    return {"code": 200, "data": contacts_data}


@router.get("/history/{target_id}")
async def get_chat_history(target_id: int, user: User = Depends(get_current_user)):
    """
    获取我和 target_id 的私信历史
    """
    # 5. 修改查询模型为 PrivateMessage
    messages = await PrivateMessage.filter(
        Q(sender_id=user.id, receiver_id=target_id) |
        Q(sender_id=target_id, receiver_id=user.id)
    ).order_by("created_at").all()

    data = []
    unread_ids = []

    for m in messages:
        if m.sender_id == target_id and not m.is_read:
            unread_ids.append(m.id)
            m.is_read = True

        data.append({
            "id": str(m.id), # UUID 转字符串
            "sender_id": m.sender_id,
            "receiver_id": m.receiver_id,
            "content": m.content,
            "created_at": m.created_at.strftime("%H:%M"),
            "is_read": m.is_read
        })

    if unread_ids:
        await PrivateMessage.filter(id__in=unread_ids).update(is_read=True)

    return {"code": 200, "data": data}