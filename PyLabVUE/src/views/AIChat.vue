<template>
  <div class="flex flex-col h-[calc(100vh-60px)] bg-gray-50">
    <div class="bg-white shadow-sm px-6 py-4 flex items-center justify-between border-b">
      <div class="flex items-center space-x-3">
        <div class="bg-indigo-100 p-2 rounded-lg">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-6 w-6 text-indigo-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
        </div>
        <div>
          <h1 class="text-lg font-bold text-gray-800">AI 智能助教</h1>
          <p class="text-xs text-gray-500">DeepSeek R1 驱动 | RAG 知识库增强</p>
        </div>
      </div>
      <el-tag type="success" effect="dark" round size="small">在线</el-tag>
    </div>

    <div class="flex-1 overflow-y-auto p-4 space-y-6" ref="chatContainer">
      <div class="flex justify-start">
        <div
          class="bg-white p-4 rounded-2xl rounded-tl-none shadow-sm max-w-[80%] border border-gray-100"
        >
          <p class="text-gray-800 text-sm leading-relaxed">
            👋 你好！我是你的编程助教。<br />
            有什么不懂的代码问题，或者想了解课程内容，随时问我！
          </p>
        </div>
      </div>

      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']"
      >
        <div
          v-if="msg.role === 'ai'"
          class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center mr-3 flex-shrink-0"
        >
          <span class="text-xs font-bold text-indigo-600">AI</span>
        </div>

        <div
          :class="[
            'p-4 rounded-2xl shadow-sm max-w-[85%] text-sm leading-relaxed overflow-hidden',
            msg.role === 'user'
              ? 'bg-indigo-600 text-white rounded-tr-none'
              : 'bg-white text-gray-800 rounded-tl-none border border-gray-100',
          ]"
        >
          <div v-if="msg.role === 'user'">{{ msg.content }}</div>

          <div v-else class="markdown-body" v-html="renderMarkdown(msg.content)"></div>

          <div
            v-if="msg.sources && msg.sources.length > 0"
            class="mt-3 pt-3 border-t border-gray-100/50"
          >
            <p class="text-xs text-gray-400 mb-1">📚 参考资料：</p>
            <ul class="space-y-1">
              <li
                v-for="(src, idx) in msg.sources"
                :key="idx"
                class="text-xs text-indigo-400 truncate hover:text-indigo-500 cursor-pointer"
              >
                - {{ src.title }}
              </li>
            </ul>
          </div>
        </div>

        <div
          v-if="msg.role === 'user'"
          class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center ml-3 flex-shrink-0"
        >
          <span class="text-xs font-bold text-gray-600">ME</span>
        </div>
      </div>

      <div v-if="loading" class="flex justify-start">
        <div class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center mr-3">
          <span class="text-xs font-bold text-indigo-600">AI</span>
        </div>
        <div
          class="bg-white p-4 rounded-2xl rounded-tl-none shadow-sm border border-gray-100 flex items-center space-x-1"
        >
          <div
            class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"
            style="animation-delay: 0ms"
          ></div>
          <div
            class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"
            style="animation-delay: 150ms"
          ></div>
          <div
            class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"
            style="animation-delay: 300ms"
          ></div>
        </div>
      </div>
    </div>

    <div class="bg-white border-t p-4">
      <div class="max-w-4xl mx-auto relative">
        <textarea
          v-model="inputMsg"
          @keydown.enter.prevent="sendMessage"
          placeholder="输入你的问题，按 Enter 发送..."
          class="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none h-[50px] max-h-[150px] scrollbar-hide text-sm"
        ></textarea>

        <button
          @click="sendMessage"
          :disabled="loading || !inputMsg.trim()"
          class="absolute right-2 top-2 p-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"
            />
          </svg>
        </button>
      </div>
      <p class="text-center text-xs text-gray-400 mt-2">内容由 AI 生成，请注意甄别</p>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/atom-one-dark.css' // 引入代码高亮样式
import axios from 'axios' // 假设你用 axios，如果封装了 request 请替换

const messages = ref([])
const inputMsg = ref('')
const loading = ref(false)
const chatContainer = ref(null)

// 配置 marked 支持代码高亮
marked.setOptions({
  highlight: function (code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext'
    return hljs.highlight(code, { language }).value
  },
  langPrefix: 'hljs language-',
})

// Markdown 渲染函数
const renderMarkdown = (content) => {
  return marked.parse(content)
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

// 发送消息
const sendMessage = async () => {
  if (!inputMsg.value.trim() || loading.value) return

  const question = inputMsg.value.trim()
  inputMsg.value = '' // 清空输入框

  // 1. 添加用户消息
  messages.value.push({ role: 'user', content: question })
  scrollToBottom()

  loading.value = true

  try {
    // 2. 调用后端接口 (请根据你实际的 axios 封装调整 URL)
    // 假设你的后端地址是 /api/ai/chat
    const res = await axios.post(
      'http://127.0.0.1:8000/ai/chat',
      {
        question: question,
      },
      {
        // 如果后端开了 Auth，这里记得带 Token
        // headers: { Authorization: `Bearer ${token}` }
      },
    )

    if (res.data.code === 200) {
      const answerText = res.data.data.answer
      const sources = res.data.data.sources || [] // 获取参考资料

      // 3. 模拟打字机效果
      const aiMsgIndex =
        messages.value.push({
          role: 'ai',
          content: '',
          sources: sources,
        }) - 1

      let i = 0
      const typeWriter = setInterval(() => {
        if (i < answerText.length) {
          messages.value[aiMsgIndex].content += answerText.charAt(i)
          i++
          scrollToBottom() // 每次打字都滚动
        } else {
          clearInterval(typeWriter)
        }
      }, 30) // 打字速度，越小越快
    } else {
      messages.value.push({ role: 'ai', content: '🤯 AI 脑子有点乱，请稍后再试。' })
    }
  } catch (error) {
    console.error(error)
    messages.value.push({ role: 'ai', content: '🔌 连接服务器失败，请检查网络。' })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}
</script>

<style>
/* Markdown 样式微调 */
.markdown-body p {
  margin-bottom: 0.5em;
}
.markdown-body pre {
  background: #282c34;
  padding: 1em;
  border-radius: 8px;
  overflow-x: auto;
  color: #abb2bf;
}
.markdown-body code {
  background: #f3f4f6;
  padding: 2px 4px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.9em;
  color: #c7254e;
}
.markdown-body pre code {
  background: transparent;
  padding: 0;
  color: inherit;
  font-size: 100%;
}
.markdown-body ul {
  list-style-type: disc;
  padding-left: 1.5em;
}
.markdown-body ol {
  list-style-type: decimal;
  padding-left: 1.5em;
}
/* 隐藏滚动条 */
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
