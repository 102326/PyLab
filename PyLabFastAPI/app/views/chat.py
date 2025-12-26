from fastapi import APIRouter, Depends
from app.deps import get_current_user
from app.models.user import User
from app.models.chat import ChatMessage
from tortoise.expressions import Q
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/chat", tags=["Chat"])


# --- 响应模型 ---
class ContactSchema(BaseModel):
    id: int
    nickname: str
    avatar: Optional[str] = None
    role: int
    last_msg: Optional[str] = None  # 最后一条消息内容
    last_time: Optional[str] = None  # 最后一条消息时间
    unread_count: int = 0  # 未读消息数


@router.get("/contacts")
async def get_recent_contacts(user: User = Depends(get_current_user)):
    """
    获取最近联系人列表（带最后一条消息和未读数）
    """
    # 1. 找出我发过消息的人 ID 集合
    # 【关键修复】Postgres要求 DISTINCT 的字段必须是 ORDER BY 的第一个字段
    sent_to_ids = await ChatMessage.filter(sender_id=user.id) \
        .order_by("receiver_id") \
        .distinct() \
        .values_list('receiver_id', flat=True)

    # 2. 找出给我发过消息的人 ID 集合
    received_from_ids = await ChatMessage.filter(receiver_id=user.id) \
        .order_by("sender_id") \
        .distinct() \
        .values_list('sender_id', flat=True)

    # 3. 合并去重
    contact_user_ids = set(sent_to_ids + received_from_ids)

    contacts_data = []

    # 4. 查询联系人详情，并填充最后消息和未读数
    if contact_user_ids:
        contacts = await User.filter(id__in=contact_user_ids).all()

        for contact in contacts:
            # A. 查最后一条消息 (我和他，或者他和我)
            last_message = await ChatMessage.filter(
                Q(sender_id=user.id, receiver_id=contact.id) |
                Q(sender_id=contact.id, receiver_id=user.id)
            ).order_by('-created_at').first()

            # B. 查未读数 (他发给我，且未读)
            unread_count = await ChatMessage.filter(
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

    # 【冷启动策略】如果是新学生且没有联系人，推荐几个老师
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

    # 按最后消息时间倒序排列 (把最近聊过的人排在前面)
    # 处理 None 值防止排序报错
    contacts_data.sort(key=lambda x: x['last_time'] or "", reverse=True)

    return {"code": 200, "data": contacts_data}


@router.get("/history/{target_id}")
async def get_chat_history(target_id: int, user: User = Depends(get_current_user)):
    """
    获取我和 target_id 的历史消息
    """
    # 1. 查询双方的对话
    messages = await ChatMessage.filter(
        Q(sender_id=user.id, receiver_id=target_id) |
        Q(sender_id=target_id, receiver_id=user.id)
    ).order_by("created_at").all()

    data = []
    # 2. 批量标记已读 (找到对方发给我的未读消息)
    unread_ids = []

    for m in messages:
        if m.sender_id == target_id and not m.is_read:
            unread_ids.append(m.id)
            m.is_read = True  # 内存中更新，方便下面返回正确状态

        data.append({
            "id": m.id,
            "sender_id": m.sender_id,
            "receiver_id": m.receiver_id,
            "content": m.content,
            "created_at": m.created_at.strftime("%H:%M"),  # 简单格式化
            "is_read": m.is_read
        })

    # 3. 数据库执行更新
    if unread_ids:
        await ChatMessage.filter(id__in=unread_ids).update(is_read=True)

    return {"code": 200, "data": data}