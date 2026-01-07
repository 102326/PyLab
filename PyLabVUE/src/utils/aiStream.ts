// PyLabVUE/src/utils/aiStream.ts

/**
 * 专门用于处理 AI 流式对话的工具函数
 * @param url 请求地址
 * @param payload 请求体 (包含 message, history)
 * @param onMessage 接收到新字符时的回调
 * @param onDone 完成时的回调
 * @param onError 出错时的回调
 */
export async function streamChat(
  url: string,
  payload: { message: string; history?: any[] },
  onMessage: (text: string) => void,
  onDone: () => void,
  onError: (err: Error) => void,
) {
  try {
    const token = localStorage.getItem('token')
    if (!token) throw new Error('未检测到登录 Token，请重新登录')

    // 1. 发起 Fetch 请求
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`, // 👈 自动携带 Token
      },
      body: JSON.stringify(payload),
    })

    // 2. 严格的错误处理
    if (!response.ok) {
      let errorMsg = `请求失败 (${response.status})`
      try {
        // 尝试读取后端返回的详细错误信息
        const errorText = await response.text()
        // 如果是 JSON 格式的错误，尝试解析
        if (errorText.startsWith('{')) {
          const errObj = JSON.parse(errorText)
          errorMsg += `: ${errObj.detail || errObj.message || errorText}`
        } else {
          errorMsg += `: ${errorText}`
        }
      } catch (e) {
        // 读取错误体失败，忽略
      }
      throw new Error(errorMsg)
    }

    if (!response.body) throw new Error('后端未返回流式响应体')

    // 3. 准备读取器
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')

    // 4. 循环读取流
    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        onDone()
        break
      }

      // 解码当前块
      const chunk = decoder.decode(value, { stream: true })
      // 回调给 UI
      onMessage(chunk)
    }
  } catch (err: any) {
    console.error('AI Stream Error:', err)
    // 确保抛出的一定是 Error 对象，避免 undefined
    const errorObj = err instanceof Error ? err : new Error(String(err))
    onError(errorObj)
  }
}
