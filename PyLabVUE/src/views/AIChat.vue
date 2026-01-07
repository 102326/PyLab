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
      <div class="flex space-x-2">
        <el-button size="small" @click="loadHistory" :loading="historyLoading">加载历史</el-button>
        <el-tag type="success" effect="dark" round size="small">在线</el-tag>
      </div>
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

          <div v-if="msg.sources" class="mt-3 pt-3 border-t border-gray-100/50">
            <p class="text-xs text-gray-400 mb-1">📚 参考资料摘要：</p>
            <p class="text-xs text-gray-500 line-clamp-3">{{ msg.sources }}</p>
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
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/atom-one-dark.css'
import axios from 'axios'
// 👇👇👇 核心：引入用户状态库
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const messages = ref([])
const inputMsg = ref('')
const loading = ref(false)
const historyLoading = ref(false)
const chatContainer = ref(null)

// Markdown 配置
marked.setOptions({
  highlight: function (code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext'
    return hljs.highlight(code, { language }).value
  },
  langPrefix: 'hljs language-',
})
const renderMarkdown = (content) => marked.parse(content)

const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

// 获取 Token 的辅助函数
const getToken = () => {
  if (userStore.token) return userStore.token
  const localToken = localStorage.getItem('token')
  if (localToken) {
    userStore.token = localToken
    return localToken
  }
  return ''
}

// 发送消息
const sendMessage = async () => {
  if (!inputMsg.value.trim() || loading.value) return

  // 1. 检查是否登录
  const token = getToken()
  if (!token) {
    ElMessage.warning('请先登录后再使用 AI 助手')
    // messages.value.push({ role: 'ai', content: '🚫 请先登录后再提问。' });
    return
  }

  const question = inputMsg.value.trim()
  inputMsg.value = ''
  messages.value.push({ role: 'user', content: question })
  scrollToBottom()
  loading.value = true

  try {
    // 2. 发起请求 (带 Header)
    const res = await axios.post(
      'http://127.0.0.1:8000/ai/chat', // 注意：vite 代理通常是 /api/ai/chat，或者直接 /ai/chat 取决于你的 rewrite 配置
      {
        message: question, // ✅ 改正这里：把 key 从 question 改为 message
        history: [], // (可选) 建议加上历史记录字段
      },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        // 如果你要处理流式响应，记得加上这个
        responseType: 'stream',
      },
    )

    if (res.data.code === 200) {
      const answerText = res.data.data.answer
      const context = res.data.data.context_preview

      // 打字机效果
      const aiMsgIndex =
        messages.value.push({
          role: 'ai',
          content: '',
          sources: context,
        }) - 1

      let i = 0
      const typeWriter = setInterval(() => {
        if (i < answerText.length) {
          messages.value[aiMsgIndex].content += answerText.charAt(i)
          i++
          scrollToBottom()
        } else {
          clearInterval(typeWriter)
        }
      }, 20)
    } else {
      messages.value.push({ role: 'ai', content: `🤯 出错了: ${res.data.msg}` })
    }
  } catch (error) {
    console.error('AI 请求失败:', error) // 👈 F12 这里的报错很重要
    // 如果是 401，提示登录过期
    if (error.response && error.response.status === 401) {
      messages.value.push({ role: 'ai', content: '🔒 登录已过期，请重新登录。' })
    } else {
      messages.value.push({
        role: 'ai',
        content: '🔌 连接服务器失败，请检查网络 (看 F12 控制台)。',
      })
    }
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

// 加载历史记录
const loadHistory = async () => {
  const token = getToken()
  if (!token) return

  historyLoading.value = true
  try {
    const res = await axios.get('http://127.0.0.1:8000/ai/history', {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (res.data.code === 200) {
      // 转换格式并倒序放入 (历史记录一般放在最上面，这里简单处理先全覆盖或追加)
      // 这里的逻辑可以根据需求优化，比如追加到 messages 头部
      const history = res.data.data
        .map((item) => [
          { role: 'user', content: item.question },
          { role: 'ai', content: item.answer },
        ])
        .flat()

      // 为了演示，我们直接替换当前消息列表（或者你可以做分页加载）
      if (history.length > 0) {
        messages.value = [...history, ...messages.value]
        ElMessage.success('历史记录已加载')
      } else {
        ElMessage.info('暂无历史记录')
      }
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('加载历史失败')
  } finally {
    historyLoading.value = false
  }
}
</script>

<style>
/* 保持原有样式 */
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
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
