<template>
  <div class="h-screen pt-4 pb-4 px-4 bg-gray-100 flex justify-center">
    <div
      class="w-full max-w-4xl bg-white rounded-xl shadow-lg overflow-hidden flex flex-col relative"
    >
      <div class="p-4 border-b border-gray-100 bg-white z-10 flex justify-between items-center">
        <div class="flex items-center gap-2">
          <div
            class="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center text-white"
          >
            <el-icon class="text-xl"><MagicStick /></el-icon>
          </div>
          <div>
            <h2 class="text-lg font-bold text-gray-800">AI 智能助教</h2>
            <p class="text-xs text-gray-500">基于本地大模型构建</p>
          </div>
        </div>
        <el-button type="info" link @click="clearHistory">清空对话</el-button>
      </div>

      <div class="flex-1 overflow-y-auto p-6 space-y-6 bg-gray-50" ref="chatContainer">
        <div
          v-if="messages.length === 0"
          class="flex flex-col items-center justify-center h-full text-gray-400 opacity-60"
        >
          <el-icon class="text-6xl mb-4"><MagicStick /></el-icon>
          <p>有什么编程问题？尽管问我吧！</p>
        </div>

        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="flex w-full"
          :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <div
            v-if="msg.role === 'assistant'"
            class="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white flex-shrink-0 mr-3 mt-1"
          >
            <el-icon><MagicStick /></el-icon>
          </div>

          <div class="max-w-[80%]">
            <div
              class="px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm whitespace-pre-wrap"
              :class="
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white rounded-tr-none'
                  : 'bg-white text-gray-800 border border-gray-200 rounded-tl-none'
              "
            >
              {{ msg.content }}
              <span
                v-if="msg.loading"
                class="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-1 align-middle"
              ></span>
            </div>
            <div
              class="text-xs text-gray-400 mt-1 px-1"
              :class="msg.role === 'user' ? 'text-right' : 'text-left'"
            >
              {{ msg.time }}
            </div>
          </div>

          <div
            v-if="msg.role === 'user'"
            class="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center text-white flex-shrink-0 ml-3 mt-1"
          >
            <el-icon><User /></el-icon>
          </div>
        </div>
      </div>

      <div class="p-4 bg-white border-t border-gray-100">
        <div class="flex gap-2 relative">
          <el-input
            v-model="input"
            type="textarea"
            :rows="1"
            :autosize="{ minRows: 1, maxRows: 4 }"
            resize="none"
            placeholder="输入您的问题 (Shift + Enter 换行)..."
            class="custom-textarea"
            @keydown.enter.prevent="handleKeydown"
          />
          <el-button
            type="primary"
            class="!h-auto !px-6 !rounded-xl"
            :loading="isLoading"
            @click="sendMessage"
            :disabled="!input.trim()"
          >
            <el-icon class="text-xl"><Position /></el-icon>
          </el-button>
        </div>
        <p class="text-xs text-center text-gray-300 mt-2">AI 生成内容仅供参考</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { MagicStick, User, Position } from '@element-plus/icons-vue'
import { AIApi } from '@/api/ai' // ⚠️ 引入新 API
import dayjs from 'dayjs'

interface Message {
  role: 'user' | 'assistant'
  content: string
  time: string
  loading?: boolean
}

const input = ref('')
const isLoading = ref(false)
const chatContainer = ref<HTMLElement>()
const messages = ref<Message[]>([])

// 发送消息
const sendMessage = async () => {
  const text = input.value.trim()
  if (!text || isLoading.value) return

  // 1. 添加用户消息
  messages.value.push({
    role: 'user',
    content: text,
    time: dayjs().format('HH:mm'),
  })
  input.value = ''
  scrollToBottom()

  // 2. 添加 AI 占位消息
  isLoading.value = true
  const aiMsgIndex =
    messages.value.push({
      role: 'assistant',
      content: '思考中...', // 初始占位
      time: dayjs().format('HH:mm'),
      loading: true,
    }) - 1
  scrollToBottom()

  try {
    // 3. 调用 API
    const res = await AIApi.chat(text)

    // 4. 更新 AI 回复
    messages.value[aiMsgIndex].content = res.reply || 'AI 暂时无法回答。'
  } catch (error) {
    messages.value[aiMsgIndex].content = '抱歉，网络连接失败，请稍后重试。'
  } finally {
    messages.value[aiMsgIndex].loading = false
    isLoading.value = false
    scrollToBottom()
  }
}

const handleKeydown = (e: KeyboardEvent) => {
  if (!e.shiftKey) {
    sendMessage()
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

const clearHistory = () => {
  messages.value = []
}
</script>

<style scoped>
/* 隐藏 Element 默认边框，打造极简输入框 */
:deep(.el-textarea__inner) {
  border: none;
  background-color: #f3f4f6;
  border-radius: 12px;
  padding: 12px;
  box-shadow: none !important;
}
:deep(.el-textarea__inner:focus) {
  background-color: #fff;
  box-shadow: 0 0 0 1px #4f46e5 !important;
}
</style>
