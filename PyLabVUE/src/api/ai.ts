// PyLabVUE/src/api/ai.ts
import request from '@/utils/request'

// 定义会话类型
export interface ChatSession {
  id: string
  title: string
  updated_at: string
}

// 定义消息类型
export interface ChatMessage {
  role: string
  content: string
}

export class AiApi {
  /**
   * 获取会话列表
   */
  static async getSessions() {
    // 泛型 <T, R> : T是响应体包装类型(默认any), R是实际返回的数据类型
    return request.get<any, ChatSession[]>('/ai/sessions')
  }

  /**
   * 新建会话
   * @param title 会话标题
   */
  static async createSession(title = '新对话') {
    return request.post<any, ChatSession>('/ai/sessions', { title })
  }

  /**
   * 删除会话
   * @param sessionId 会话ID
   */
  static async deleteSession(sessionId: string) {
    return request.delete<any, { ok: boolean }>(`/ai/sessions/${sessionId}`)
  }

  /**
   * 获取特定会话的历史记录 (用于回显)
   * @param sessionId 会话ID
   */
  static async getHistory(sessionId: string) {
    return request.get<any, ChatMessage[]>(`/ai/sessions/${sessionId}/history`)
  }
}
