// PyLabVUE/src/api/ai.ts
import request from '@/utils/request'
import type { ChatReq } from '@/model/ai' // 假设你保留了这个类型定义

export interface ChatSession {
  id: string
  title: string
  updated_at: string
}

export class AiApi {
  // 获取会话列表
  static async getSessions() {
    return request.get<any, ChatSession[]>('/ai/sessions')
  }

  // 新建会话
  static async createSession(title = '新对话') {
    return request.post<any, ChatSession>('/ai/sessions', { title })
  }

  // 删除会话
  static async deleteSession(sessionId: string) {
    return request.delete(`/ai/sessions/${sessionId}`)
  }

  // 获取某个会话的历史记录 (非流式，用于回显)
  static async getHistory(sessionId: string) {
    return request.get<any, Array<{ role: string; content: string }>>(
      `/ai/sessions/${sessionId}/history`,
    )
  }

  // (流式对话逻辑依然推荐走 aiStream.ts，这里只留作类型参考)
}
