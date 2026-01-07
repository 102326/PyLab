<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/atom-one-dark.css'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, ChatLineRound, Message } from '@element-plus/icons-vue'
import { AiApi, type ChatSession } from '@/api/ai'
import { streamChat } from '@/utils/aiStream'

// === 状态定义 ===
const sessions = ref<ChatSession[]>([])
const currentSessionId = ref<string>('')
const messages = ref<Array<{ role: 'user' | 'assistant'; content: string; isStreaming?: boolean }>>(
  [],
)
const inputMsg = ref('')
const isLoading = ref(false)
const isSidebarOpen = ref(true)
const chatBodyRef = ref<HTMLElement | null>(null)

// === Markdown 配置 ===
marked.setOptions({
  highlight: (code, lang) => {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext'
    return hljs.highlight(code, { language }).value
  },
  langPrefix: 'hljs language-',
})
const renderMarkdown = (content: string) => marked.parse(content || '')

// === 核心逻辑 ===

// 1. 加载会话列表
const loadSessions = async () => {
  try {
    const res = await AiApi.getSessions()
    sessions.value = Array.isArray(res) ? res : (res as any).data || []

    // 初始化：如果不为空且未选中，选中第一个
    if (!currentSessionId.value && sessions.value.length > 0) {
      // 这里的 true 表示是初始化加载，不进行清屏闪烁
      await switchSession(sessions.value[0].id)
    }
  } catch (err) {
    console.error('加载会话失败', err)
  }
}

// 2. 切换会话 (核心修改：避免不必要的闪烁)
const switchSession = async (sessionId: string) => {
  if (isLoading.value) return ElMessage.warning('请等待当前对话结束')

  // 如果点击的是当前会话，不做任何事
  if (currentSessionId.value === sessionId) return

  currentSessionId.value = sessionId
  messages.value = [] // 切换会话时才清屏

  try {
    const history = await AiApi.getHistory(sessionId)
    messages.value = (Array.isArray(history) ? history : (history as any).data || []).map(
      (m: any) => ({
        role: m.role === 'user' ? 'user' : 'assistant',
        content: m.content,
      }),
    )
    await scrollToBottom()
  } catch (err) {
    ElMessage.error('加载历史记录失败')
  }
}

// 3. 手动点击“新建对话”按钮
const handleCreateAndSwitch = async () => {
  if (isLoading.value) return
  currentSessionId.value = '' // 置空 ID
  messages.value = [] // 清屏
  // 注意：我们不立即请求后端创建，而是等用户发第一条消息时才创建 (懒加载模式)，
  // 或者你希望立即创建也可以，但懒加载体验更好，不会产生一堆空会话。
  // 如果你非要立即创建：
  /*
  const newSession = await createSessionInternal()
  sessions.value.unshift(newSession)
  currentSessionId.value = newSession.id
  */
}

// 内部工具：纯创建 Session 数据，不操作 UI
const createSessionInternal = async (title?: string) => {
  try {
    const res = await AiApi.createSession(title)
    return (res as any).data || res
  } catch (err) {
    throw new Error('创建会话失败')
  }
}

// 4. 删除会话
const handleDeleteSession = async (sessionId: string, event: Event) => {
  event.stopPropagation()
  try {
    await ElMessageBox.confirm('确定要删除这个对话吗？', '提示', { type: 'warning' })
    await AiApi.deleteSession(sessionId)
    sessions.value = sessions.value.filter((s) => s.id !== sessionId)
    if (sessionId === currentSessionId.value) {
      if (sessions.value.length > 0) {
        switchSession(sessions.value[0].id)
      } else {
        currentSessionId.value = ''
        messages.value = []
      }
    }
  } catch {}
}

// 5. 发送消息 (🔥 修复闪烁的核心)
const handleSend = async () => {
  const text = inputMsg.value.trim()
  if (!text || isLoading.value) return

  // 1. 用户消息立即上屏
  messages.value.push({ role: 'user', content: text })
  inputMsg.value = ''
  isLoading.value = true
  await scrollToBottom()

  try {
    // 2. 检查是否需要新建会话
    if (!currentSessionId.value) {
      // ⚡️ 这一步静默创建，绝不要清空 messages！
      const newSession = await createSessionInternal(text.slice(0, 10)) // 用前10个字做标题
      sessions.value.unshift(newSession) // 加到列表顶部
      currentSessionId.value = newSession.id // 绑定 ID
      // 注意：这里不要调 switchSession，因为屏幕上已经有刚才发的那条消息了
    }

    // 3. 准备 AI 气泡
    const aiMsgIndex =
      messages.value.push({ role: 'assistant', content: '', isStreaming: true }) - 1

    // 4. 发起流式请求
    const API_URL = `/api/ai/chat/${currentSessionId.value}`

    await streamChat(
      API_URL,
      { message: text },
      (chunk) => {
        // 实时更新 UI
        messages.value[aiMsgIndex].content += chunk
        // 使用 requestAnimationFrame 节流滚动，防止卡顿
        requestAnimationFrame(() => scrollToBottom())
      },
      () => {
        // 完成
        isLoading.value = false
        messages.value[aiMsgIndex].isStreaming = false
      },
      (err) => {
        // 出错
        isLoading.value = false
        messages.value[aiMsgIndex].isStreaming = false
        messages.value[aiMsgIndex].content += `\n\n❌ Error: ${err.message}`
      },
    )
  } catch (err: any) {
    isLoading.value = false
    ElMessage.error(err.message || '发送失败')
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatBodyRef.value) {
    chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight
  }
}

// 初始化
onMounted(() => {
  loadSessions()
})
</script>

<template>
  <div class="flex h-[calc(100vh-60px)] bg-gray-50 overflow-hidden">
    <div
      :class="[
        'w-64 bg-gray-900 flex flex-col transition-all duration-300 flex-shrink-0',
        isSidebarOpen ? 'translate-x-0' : '-translate-x-64 hidden md:flex md:translate-x-0',
      ]"
    >
      <div class="p-4">
        <button
          @click="handleCreateAndSwitch"
          class="w-full flex items-center gap-2 px-4 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors border border-indigo-500 shadow-sm"
        >
          <el-icon><Plus /></el-icon>
          <span class="text-sm font-medium">新建对话</span>
        </button>
      </div>

      <div class="flex-1 overflow-y-auto px-2 space-y-1 custom-scrollbar">
        <div
          v-for="session in sessions"
          :key="session.id"
          @click="switchSession(session.id)"
          :class="[
            'group flex items-center justify-between p-3 rounded-lg cursor-pointer text-sm transition-colors',
            currentSessionId === session.id
              ? 'bg-gray-800 text-white'
              : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200',
          ]"
        >
          <div class="flex items-center gap-3 overflow-hidden">
            <el-icon><ChatLineRound /></el-icon>
            <span class="truncate">{{ session.title || '新对话' }}</span>
          </div>
          <button
            @click.stop="(e) => handleDeleteSession(session.id, e)"
            class="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition-opacity"
          >
            <el-icon><Delete /></el-icon>
          </button>
        </div>
      </div>
    </div>

    <div class="flex-1 flex flex-col min-w-0 bg-white">
      <div class="h-14 border-b flex items-center justify-between px-4 bg-white shadow-sm z-10">
        <div class="flex items-center gap-2">
          <button @click="isSidebarOpen = !isSidebarOpen" class="md:hidden p-2 text-gray-600">
            <el-icon><Message /></el-icon>
          </button>
          <span class="font-bold text-gray-700 truncate max-w-[200px]">
            {{ sessions.find((s) => s.id === currentSessionId)?.title || '新话题' }}
          </span>
        </div>
        <div
          class="text-xs text-green-600 bg-green-50 px-2 py-1 rounded-full flex items-center gap-1"
        >
          <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
          DeepSeek R1
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-4 space-y-6" ref="chatBodyRef">
        <div
          v-if="messages.length === 0"
          class="h-full flex flex-col items-center justify-center text-gray-400 space-y-4"
        >
          <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center text-2xl">
            👋
          </div>
          <p>有什么可以帮你的吗？</p>
        </div>

        <div
          v-for="(msg, index) in messages"
          :key="index"
          :class="['flex w-full', msg.role === 'user' ? 'justify-end' : 'justify-start']"
        >
          <div
            v-if="msg.role === 'assistant'"
            class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center mr-3 flex-shrink-0 text-xs"
          >
            AI
          </div>
          <div
            :class="[
              'max-w-[85%] md:max-w-[70%] p-4 rounded-2xl shadow-sm text-sm leading-7',
              msg.role === 'user'
                ? 'bg-indigo-600 text-white rounded-tr-none'
                : 'bg-gray-50 text-gray-800 border border-gray-100 rounded-tl-none',
            ]"
          >
            <div v-if="msg.role === 'user'" class="whitespace-pre-wrap">{{ msg.content }}</div>
            <div v-else class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
            <span
              v-if="msg.isStreaming"
              class="inline-block w-1.5 h-4 bg-indigo-500 ml-1 animate-pulse align-middle"
            ></span>
          </div>
          <div
            v-if="msg.role === 'user'"
            class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center ml-3 flex-shrink-0 text-xs"
          >
            Me
          </div>
        </div>
      </div>

      <div class="p-4 border-t bg-white">
        <div class="max-w-4xl mx-auto relative">
          <textarea
            v-model="inputMsg"
            @keydown.enter.prevent="handleSend"
            :disabled="isLoading"
            placeholder="输入您的问题..."
            class="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none h-[52px] max-h-[150px] scrollbar-hide text-sm"
          ></textarea>
          <button
            @click="handleSend"
            :disabled="isLoading || !inputMsg.trim()"
            class="absolute right-2 top-2.5 p-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
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
  </div>
</template>
