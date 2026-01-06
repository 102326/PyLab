// src/api/ai.ts
import request from '@/utils/request'
import type { ApiResponse } from '@/model/common'

export interface AIChatRes {
  reply: string
}

export class AIApi {
  /**
   * 发送消息给 AI
   * @param content 用户输入的问题
   */
  static async chat(content: string) {
    // 假设后端接口是 /chat/ai 或者复用 /chat/semantic
    // 这里我们假设后端有一个专门处理对话的接口
    // 如果没有，可以先用 /chat/semantic 凑合，或者在后端 app/views/chat.py 加一个
    const res = await request.post<ApiResponse<AIChatRes>>('/chat/ask', {
      question: content,
    })
    return res.data.data
  }
}
