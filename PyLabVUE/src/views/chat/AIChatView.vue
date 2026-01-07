<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/atom-one-dark.css' // 确保你安装了样式
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, ChatLineRound, Message, Fold, Expand } from '@element-plus/icons-vue'
import { AiApi, type ChatSession } from '@/api/ai'
import { streamChat } from '@/utils/aiStream'

// === 状态管理 ===
const sessions = ref<ChatSession[]>([])
const currentSessionId = ref<string>('')
const messages = ref<Array<{ role: 'user' | 'assistant'; content: string; isStreaming?: boolean }>>([])
const inputMsg = ref('')
const isLoading = ref(false)
const isSidebarOpen = ref(true) // 侧边栏开关
const chatBodyRef = ref<HTMLElement | null>(null)

// === Markdown 配置 ===
marked.setOptions({
  highlight: (code, lang) => {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext'
    return hljs.highlight(code, { language }).value
  },
  langPrefix: 'hljs language-',
  breaks: true // 自动换行
})
const renderMarkdown = (content: string) => marked.parse(content || '')

// === 业务逻辑 ===

/**
 * 1. 加载会话列表
 */
const loadSessions = async () => {
  try {
    const res = await AiApi.getSessions()
    // 兼容不同的响应结构 (直接数组 或 { data: [] })
    sessions.value = Array.isArray(res) ? res : (res as any).data || []

    // 初始化：如果不为空且当前未选中，默认选中最新的一个
    if (!currentSessionId.value && sessions.value.length > 0) {
      await switchSession(sessions.value[0].id)
    }
  } catch (err) {
    console.error('加载会话失败', err)
    ElMessage.error('无法加载历史会话')
  }
}

/**
 * 2. 切换会话
 */
const switchSession = async (sessionId: string) => {
  if (isLoading.value) return ElMessage.warning('请等待当前回复生成完毕')
  if (currentSessionId.value === sessionId) return

  currentSessionId.value = sessionId
  messages.value = [] // 切换时才清空

  try {
    const res = await AiApi.getHistory(sessionId)
    const history = Array.isArray(res) ? res : (res as any).data || []

    // 格式化消息
    messages.value = history.map((m: any) => ({
      role: m.role === 'user' ? 'user' : 'assistant', // 统一转换角色名
      content: m.content
    }))

    await scrollToBottom()
  } catch (err) {
    ElMessage.error('加载历史记录失败')
  }
}

/**
 * 3. 点击“新建对话” (UI 逻辑)
 * 此时不请求后端，只清空界面，等用户发消息时再创建
 */
const handleNewChatUI = () => {
  if (isLoading.value) return
  currentSessionId.value = '' // 置空 ID
  messages.value = [] // 清空消息
  // 移动端新建后自动收起侧边栏
  if (window.innerWidth < 768) isSidebarOpen.value = false
}

/**
 * 4. 删除会话
 */
const handleDeleteSession = async (sessionId: string, event: Event) => {
  event.stopPropagation() // 阻止冒泡
  try {
    await ElMessageBox.confirm('确定要永久删除这个对话吗？', '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })

    await AiApi.deleteSession(sessionId)
    sessions.value = sessions.value.filter(s => s.id !== sessionId)

    // 如果删的是当前选中的
    if (sessionId === currentSessionId.value) {
      if (sessions.value.length > 0) {
        switchSession(sessions.value[0].id)
      } else {
        handleNewChatUI()
      }
    }
    ElMessage.success('已删除')
  } catch {
    // 取消删除
  }
}

/**
 * 5. 发送消息 (核心：无闪烁逻辑)
 */
const handleSend = async () => {
  const text = inputMsg.value.trim()
  if (!text || isLoading.value) return

  // A. 用户消息立即上屏
  messages.value.push({ role: 'user', content: text })
  inputMsg.value = ''
  isLoading.value = true
  await scrollToBottom()

  try {
    // B. 检查是否需要新建会话
    if (!currentSessionId.value) {
      // 使用前 15 个字作为标题
      const title = text.length > 15 ? text.slice(0, 15) + '...' : text
      // 静默创建
      const res = await AiApi.createSession(title)
      const newSession = (res as any).data || res // 兼容处理

      // 更新状态，不清空 messages
      sessions.value.unshift(newSession)
      currentSessionId.value = newSession.id
    }

    // C. 准备 AI 占位气泡
    const aiMsgIndex = messages.value.push({ role: 'assistant', content: '', isStreaming: true }) - 1

    // D. 发起流式请求
    // 此时 currentSessionId 一定有值
    const API_URL = `/api/ai/chat/${currentSessionId.value}`

    await streamChat(
      API_URL,
      { message: text },
      (chunk) => {
        // 收到数据块
        messages.value[aiMsgIndex].content += chunk
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
        messages.value[aiMsgIndex].content += `\n\n❌ **Error**: ${err.message}`
      }
    )

  } catch (err: any) {
    isLoading.value = false
    ElMessage.error(err.message || '发送失败')
  }
}

// 滚动到底部
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
  <div class="flex h-[calc(100vh-60px)] bg-gray-50 overflow-hidden relative">

    <div
      :class="[
        'bg-gray-900 flex flex-col transition-all duration-300 ease-in-out z-20',
        isSidebarOpen ? 'w-64 translate-x-0' : 'w-0 -translate-x-full md:w-0 md:translate-x-0 opacity-0 md:opacity-100 overflow-hidden'
      ]"
      class="absolute md:relative h-full shadow-xl md:shadow-none"
    >
      <div class="p-4 flex-shrink-0">
        <button
          @click="handleNewChatUI"
          class="w-full flex items-center justify-center gap-2 px-4 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors border border-indigo-500 shadow-sm"
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
          :class="['group flex items-center justify-between p-3 rounded-lg cursor-pointer text-sm transition-all',
            currentSessionId === session.id
              ? 'bg-gray-800 text-white shadow-sm'
              : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200']"
        >
          <div class="flex items-center gap-3 overflow-hidden flex-1">
            <el-icon class="flex-shrink-0"><ChatLineRound /></el-icon>
            <span class="truncate">{{ session.title || '无标题' }}</span>
          </div>

          <button
            @click.stop="(e) => handleDeleteSession(session.id, e)"
            class="opacity-0 group-hover:opacity-100 p-1.5 text-gray-500 hover:text-red-400 hover:bg-gray-700 rounded transition-all"
            title="删除对话"
          >
            <el-icon><Delete /></el-icon>
          </button>
        </div>

        <div v-if="sessions.length === 0" class="text-center text-gray-600 mt-10 text-xs">
          暂无历史对话
        </div>
      </div>

      <div class="p-4 border-t border-gray-800 text-gray-600 text-xs text-center flex-shrink-0">
        PyLab AI v2.1
      </div>
    </div>

    <div class="flex-1 flex flex-col min-w-0 bg-white relative">

      <div class="h-14 border-b flex items-center justify-between px-4 bg-white shadow-sm z-10">
        <div class="flex items-center gap-3">
          <button
            @click="isSidebarOpen = !isSidebarOpen"
            class="p-2 text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
          >
            <el-icon v-if="isSidebarOpen"><Fold /></el-icon>
            <el-icon v-else><Expand /></el-icon>
          </button>

          <span class="font-bold text-gray-700 truncate max-w-[200px] md:max-w-md">
             {{ sessions.find(s => s.id === currentSessionId)?.title || '新话题' }}
           </span>
        </div>

        <div class="flex items-center gap-2">
          <div class="text-xs text-green-600 bg-green-50 px-2 py-1 rounded-full flex items-center gap-1">
            <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            <span class="hidden md:inline">DeepSeek R1 Online</span>
          </div>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-4 space-y-6 scroll-smooth" ref="chatBodyRef">

        <div v-if="messages.length === 0" class="h-full flex flex-col items-center justify-center text-gray-400 space-y-6">
          <div class="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center shadow-inner">
            <span class="text-4xl">👋</span>
          </div>
          <div class="text-center space-y-2">
            <p class="text-lg text-gray-600 font-medium">有什么可以帮你的吗？</p>
            <p class="text-xs text-gray-400">支持上下文记忆 · 代码高亮 · 极速响应</p>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-lg px-4">
            <button @click="inputMsg = '解释一下 Python 的装饰器'; handleSend()" class="text-sm bg-gray-50 hover:bg-gray-100 p-3 rounded-lg border border-gray-200 text-left transition-colors">
              🚀 解释一下 Python 的装饰器
            </button>
            <button @click="inputMsg = '写一个冒泡排序算法'; handleSend()" class="text-sm bg-gray-50 hover:bg-gray-100 p-3 rounded-lg border border-gray-200 text-left transition-colors">
              💻 写一个冒泡排序算法
            </button>
          </div>
        </div>

        <div
          v-for="(msg, index) in messages"
          :key="index"
          :class="['flex w-full animate-fade-in', msg.role === 'user' ? 'justify-end' : 'justify-start']"
        >
          <div v-if="msg.role === 'assistant'" class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center mr-3 flex-shrink-0 text-xs shadow-sm border border-indigo-200 text-indigo-600 font-bold">
            AI
          </div>

          <div
            :class="[
              'max-w-[85%] md:max-w-[75%] p-4 rounded-2xl shadow-sm text-sm leading-7',
              msg.role === 'user'
                ? 'bg-indigo-600 text-white rounded-tr-none'
                : 'bg-white text-gray-800 border border-gray-100 rounded-tl-none'
            ]"
          >
            <div v-if="msg.role === 'user'" class="whitespace-pre-wrap font-sans">{{ msg.content }}</div>

            <div v-else class="markdown-body" v-html="renderMarkdown(msg.content)"></div>

            <span v-if="msg.isStreaming" class="inline-block w-1.5 h-4 bg-indigo-500 ml-1 animate-pulse align-middle"></span>
          </div>

          <div v-if="msg.role === 'user'" class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center ml-3 flex-shrink-0 text-xs border border-gray-300 text-gray-500 font-bold">
            Me
          </div>
        </div>
      </div>

      <div class="p-4 border-t bg-white relative z-20">
        <div class="max-w-4xl mx-auto relative">
          <textarea
            v-model="inputMsg"
            @keydown.enter.prevent="handleSend"
            :disabled="isLoading"
            placeholder="输入您的问题 (Shift+Enter 换行)..."
            class="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 pr-14 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all resize-none h-[52px] max-h-[150px] scrollbar-hide text-sm shadow-inner"
          ></textarea>

          <button
            @click="handleSend"
            :disabled="isLoading || !inputMsg.trim()"
            class="absolute right-2 top-2.5 p-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md active:scale-95"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
            </svg>
          </button>
        </div>
        <p class="text-center text-[10px] text-gray-400 mt-2 select-none">
          内容由 AI 生成，可能存在误差，请注意甄别
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 侧边栏滚动条美化 */
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #374151;
  border-radius: 2px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #4b5563;
}

/* 简单的淡入动画 */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in {
  animation: fadeIn 0.3s ease-out forwards;
}

/* Markdown 样式覆盖 (配合 atom-one-dark) */
:deep(.markdown-body ul) { list-style-type: disc; padding-left: 1.5em; margin: 0.5em 0; }
:deep(.markdown-body ol) { list-style-type: decimal; padding-left: 1.5em; margin: 0.5em 0; }
:deep(.markdown-body p) { margin-bottom: 0.8em; }
:deep(.markdown-body blockquote) { border-left: 4px solid #e5e7eb; padding-left: 1em; color: #6b7280; margin: 1em 0; }
:deep(.markdown-body pre) { background: #282c34 !important; padding: 1em; border-radius: 8px; overflow-x: auto; color: #abb2bf; margin: 1em 0; }
:deep(.markdown-body code) { background: #f3f4f6; color: #c7254e; padding: 2px 4px; border-radius: 4px; font-family: monospace; font-size: 0.9em; }
:deep(.markdown-body pre code) { background: transparent; color: inherit; padding: 0; border: none; }
:deep(.markdown-body a) { color: #4f46e5; text-decoration: underline; }
</style>
