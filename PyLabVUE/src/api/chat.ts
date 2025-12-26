// src/api/chat.ts
import request from '@/utils/request'
import type { ApiResponse } from '@/model/common'
import type { ChatContact, ChatMessage } from '@/model/chat'

export class ChatApi {
  /**
   * 获取最近联系人列表
   */
  static async getContacts(): Promise<ChatContact[]> {
    const res = await request.get<ApiResponse<ChatContact[]>>('/chat/contacts')
    return res.data.data
  }

  /**
   * 获取与某人的历史记录
   */
  static async getHistory(targetId: number): Promise<ChatMessage[]> {
    const res = await request.get<ApiResponse<ChatMessage[]>>(`/chat/history/${targetId}`)
    return res.data.data
  }
}
