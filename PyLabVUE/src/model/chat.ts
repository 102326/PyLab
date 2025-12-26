// src/model/chat.ts

/**
 * 联系人信息
 */
export interface ChatContact {
  id: number
  nickname: string
  avatar: string | null
  role: number // 0=学生, 1=老师
  last_msg?: string
  last_time?: string
  unread_count?: number // 前端维护的未读数
}

/**
 * 聊天消息
 */
export interface ChatMessage {
  id?: number // 发送时可能还没ID
  sender_id: number
  receiver_id: number
  content: string
  created_at: string // "HH:mm"
  is_read?: boolean
  is_self?: boolean // 辅助字段：是否是自己发的
}
