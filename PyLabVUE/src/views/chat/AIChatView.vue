<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
// 不需要引入 axios，直接用 fetch

const inputMessage = ref('')
const messages = ref<Array<{ role: 'user' | 'assistant'; content: string }>>([])
const isLoading = ref(false)

// 核心修复：使用 fetch 处理流式响应
const sendToAI = async () => {
  if (!inputMessage.value.trim()) return

  // 1.先把用户的问题上屏
  const userMsg = inputMessage.value
  messages.value.push({ role: 'user', content: userMsg })
  inputMessage.value = '' // 清空输入框
  isLoading.value = true

  // 2. 预先放入一个空的 AI 回复，用于后续拼接流
  const aiMsgIndex = messages.value.push({ role: 'assistant', content: '' }) - 1

  try {
    const token = localStorage.getItem('token') // 别忘了拿 Token

    // 【重点】使用 fetch
    const response = await fetch('/api/ai/chat', {
      // 注意路径，如果是 vite 代理，保留 /api
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`, // 👈 必须带 Header
      },
      body: JSON.stringify({
        message: userMsg,
        history: [], // 暂时传空，后续可以把 messages.value 转换一下传过去
      }),
    })

    if (!response.ok) {
      // 处理 401/422/500 错误
      const errorText = await response.text()
      throw new Error(`请求失败 (${response.status}): ${errorText}`)
    }

    if (!response.body) throw new Error('没有收到流式响应')

    // 3. 核心流式读取逻辑
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      // 解码二进制块为文本
      const chunk = decoder.decode(value, { stream: true })

      // ⚡️ 实时拼接内容，实现打字机效果
      messages.value[aiMsgIndex].content += chunk
    }
  } catch (error: any) {
    console.error('流式请求出错:', error)
    messages.value[aiMsgIndex].content += `\n[出错了: ${error.message}]`
    ElMessage.error(error.message)
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="chat-container">
    <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
      <div class="content whitespace-pre-wrap">{{ msg.content }}</div>
    </div>

    <div class="input-area">
      <input
        v-model="inputMessage"
        @keyup.enter="sendToAI"
        :disabled="isLoading"
        placeholder="问点什么..."
        class="border p-2 w-full rounded"
      />
      <button @click="sendToAI" :disabled="isLoading">发送</button>
    </div>
  </div>
</template>
