// src/api/ai.ts
import request from '@/utils/request'
import type { ChatReq } from '@/model/ai'

export class AiApi {
  static async chat(data: ChatReq) {
    // request 已经封装了 baseURL 和 Token 拦截器，不用手动写 header
    // 注意：如果是流式响应，axios 处理起来比较麻烦，建议用 fetch 或专门的流式库
    // 这里演示普通调用，流式调用推荐在组件内用 fetch + EventSourceParser
    return request.post('/ai/chat', data, {
      responseType: 'stream', // 如果是流式
    })
  }
}
