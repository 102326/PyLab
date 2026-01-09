<template>
  <div class="h-screen pt-4 pb-4 px-4 bg-gray-100 flex justify-center">
    <div class="w-full max-w-6xl bg-white rounded-xl shadow-lg overflow-hidden flex">
      <div class="w-80 bg-gray-50 border-r border-gray-200 flex flex-col">
        <div class="p-4 border-b border-gray-200 bg-white">
          <h2 class="text-lg font-bold text-gray-800">消息中心</h2>
        </div>

        <div class="flex-1 overflow-y-auto">
          <div
            v-for="contact in chatStore.contacts"
            :key="contact.id"
            @click="handleSelect(contact.id)"
            class="p-4 flex items-center cursor-pointer transition-colors hover:bg-gray-100 relative"
            :class="{ 'bg-blue-50': chatStore.currentDestId === contact.id }"
          >
            <el-avatar
              :size="40"
              :src="contact.avatar || ''"
              class="flex-shrink-0 bg-blue-500 text-white select-none"
            >
              {{ contact.nickname.charAt(0) }}
            </el-avatar>

            <div class="ml-3 flex-1 min-w-0">
              <div class="flex justify-between items-baseline mb-1">
                <span class="font-medium text-gray-900 truncate">{{ contact.nickname }}</span>
                <span class="text-xs text-gray-400">{{ formatTime(contact.last_time) }}</span>
              </div>
              <p class="text-sm text-gray-500 truncate">
                {{ isAudio(contact.last_msg) ? '[语音消息]' : contact.last_msg || '暂无消息' }}
              </p>
            </div>

            <div
              v-if="contact.unread_count && contact.unread_count > 0"
              class="absolute top-2 right-2 min-w-[18px] h-[18px] px-1 bg-red-500 text-white text-xs rounded-full flex items-center justify-center"
            >
              {{ contact.unread_count }}
            </div>
          </div>
        </div>
      </div>

      <div class="flex-1 flex flex-col bg-white">
        <div
          v-if="!chatStore.currentDestId"
          class="flex-1 flex flex-col items-center justify-center text-gray-400"
        >
          <el-icon class="text-6xl mb-4"><ChatLineRound /></el-icon>
          <p>选择一个联系人开始聊天</p>
        </div>

        <template v-else>
          <div class="p-4 border-b border-gray-200 flex items-center justify-between">
            <span class="font-bold text-lg text-gray-800">{{ currentContact?.nickname }}</span>
            <el-tag size="small" :type="currentContact?.role === 1 ? 'success' : 'info'">
              {{ currentContact?.role === 1 ? '老师' : '学员' }}
            </el-tag>
          </div>

          <div class="flex-1 overflow-y-auto p-6 space-y-6 bg-gray-50" ref="msgContainer">
            <div
              v-for="(msg, idx) in currentMessages"
              :key="idx"
              class="flex w-full"
              :class="msg.is_self ? 'justify-end' : 'justify-start'"
            >
              <el-avatar
                v-if="!msg.is_self"
                :size="36"
                class="mr-3 bg-gray-400 flex-shrink-0"
                :src="currentContact?.avatar || ''"
              >
                {{ currentContact?.nickname?.charAt(0) }}
              </el-avatar>

              <div class="flex flex-col max-w-[70%]">
                <div
                  class="px-4 py-2 rounded-lg text-sm shadow-sm break-words"
                  :class="[
                    msg.is_self
                      ? 'bg-blue-600 text-white rounded-tr-none'
                      : 'bg-white text-gray-800 border border-gray-200 rounded-tl-none',
                    // 如果是语音消息，鼠标变成手型
                    isAudio(msg.content) ? 'cursor-pointer hover:opacity-90' : '',
                  ]"
                  @click="isAudio(msg.content) ? playAudio(msg.content) : null"
                >
                  <template v-if="isAudio(msg.content)">
                    <div class="flex items-center gap-2 select-none min-w-[80px]">
                      <span class="text-lg">🔊</span>
                      <span>{{ '语音消息' }}</span>
                    </div>
                  </template>
                  <template v-else-if="isImage(msg.content)">
                    <el-image
                      :src="msg.content"
                      :preview-src-list="[msg.content]"
                      class="max-w-[200px] rounded cursor-pointer"
                      fit="cover"
                    />
                  </template>

                  <template v-else>
                    {{ msg.content }}
                  </template>
                </div>

                <span
                  class="text-xs text-gray-400 mt-1"
                  :class="msg.is_self ? 'text-right' : 'text-left'"
                >
                  {{ msg.created_at }}
                </span>
              </div>

              <el-avatar
                v-if="msg.is_self"
                :size="36"
                class="ml-3 bg-indigo-600 flex-shrink-0"
                :src="userStore.userInfo?.avatar || ''"
              >
                {{ userStore.userInfo?.nickname?.charAt(0) }}
              </el-avatar>
            </div>
          </div>

          <div class="p-4 border-t border-gray-200">
            <div class="flex gap-2 items-center">
              <button
                class="flex-shrink-0 w-12 h-10 flex items-center justify-center rounded transition-all select-none"
                :class="
                  isRecording
                    ? 'bg-red-500 text-white animate-pulse'
                    : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                "
                @mousedown.prevent="startRecording"
                @mouseup.prevent="handleSendAudio"
                @touchstart.prevent="startRecording"
                @touchend.prevent="handleSendAudio"
                title="按住说话"
              >
                <span v-if="isRecording" class="font-bold text-xs">松开</span>
                <span v-else class="text-xl">🎤</span>
              </button>

              <el-input
                v-model="inputContent"
                placeholder="请输入消息... (支持 Ctrl+V 粘贴截图)"
                @keyup.enter="handleSend"
                @paste="handlePaste"
                class="flex-1"
                size="large"
              />

              <el-button
                type="primary"
                size="large"
                @click="handleSend"
                :disabled="!inputContent.trim()"
              >
                发送
              </el-button>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue' // [修改] 引入 onUnmounted
import { useRoute } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { useSocketStore } from '@/stores/socket'
import { useUserStore } from '@/stores/user'
import { ChatLineRound } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { ElLoading } from 'element-plus'
import confetti from 'canvas-confetti'

// 1. 引入录音 Hook 和上传 API
import { useAudioRecorder } from '@/composables/useAudioRecorder'
import { uploadFile } from '@/api/media'

const chatStore = useChatStore()
const socketStore = useSocketStore()
const userStore = useUserStore()
const route = useRoute()

const inputContent = ref('')
const msgContainer = ref<HTMLElement>()

// 解构录音相关状态和方法
const { isRecording, audioBlob, startRecording, stopRecording } = useAudioRecorder()

const currentContact = computed(() =>
  chatStore.contacts.find((c) => c.id === chatStore.currentDestId),
)

const currentMessages = computed(() =>
  chatStore.currentDestId ? chatStore.messages[chatStore.currentDestId] || [] : [],
)

// === 核心逻辑1：判断是否为语音消息 ===
const isAudio = (content?: string) => {
  if (!content) return false
  const lower = content.toLowerCase()
  return (
    lower.endsWith('.mp3') ||
    lower.endsWith('.wav') ||
    lower.endsWith('.webm') ||
    lower.endsWith('.ogg') ||
    lower.endsWith('.m4a') ||
    (lower.startsWith('http') && lower.includes('voice_'))
  )
}
const isImage = (content?: string) => {
  if (!content) return false
  const lower = content.toLowerCase()
  return (
    lower.endsWith('.png') ||
    lower.endsWith('.jpg') ||
    lower.endsWith('.jpeg') ||
    lower.endsWith('.gif') ||
    lower.endsWith('.webp')
  )
}

// === 核心逻辑2：播放语音 ===
const playAudio = (url: string) => {
  const audio = new Audio(url)
  audio.play().catch((e) => {
    ElMessage.error('播放失败，音频可能已过期')
    console.error(e)
  })
}
// 录音功能
const handleSendAudio = async () => {
  console.log('正在停止录音...')

  // 1. 等待录音文件生成
  const blob = await stopRecording()

  if (!blob) {
    console.warn('录音取消或异常')
    return
  }

  // 简单校验
  if (blob.size < 1000) {
    ElMessage.warning('说话时间太短了')
    return
  }

  try {
    ElMessage.success('正在发送语音...')
    // 2. 上传到后端
    const res = await uploadFile(blob)

    // 3. 拿到 URL 发送
    const audioUrl = res.data.data.url

    if (!audioUrl) throw new Error('URL为空')

    const targetId = chatStore.currentDestId
    if (!targetId) return

    socketStore.send({
      type: 'chat',
      to_user_id: targetId,
      content: audioUrl,
    })

    // 本地显示
    chatStore.addMessage({
      sender_id: userStore.userInfo?.id || 0,
      receiver_id: targetId,
      content: audioUrl,
      created_at: dayjs().format('HH:mm'),
      is_self: true,
    })
  } catch (e) {
    console.error('语音发送失败', e)
    ElMessage.error('语音发送失败，请重试')
  }
}

const handlePaste = async (event: ClipboardEvent) => {
  // 1. 获取剪贴板里的内容
  const items = event.clipboardData?.items
  if (!items) return

  // 2. 遍历查找是否有图片文件
  let imageFile: File | null = null
  for (const item of items) {
    if (item.type.indexOf('image') !== -1) {
      imageFile = item.getAsFile()
      break
    }
  }

  // 如果没找到图片，就当作普通粘贴，不阻止默认行为（让文字上屏）
  if (!imageFile) return

  try {
    // 4. 确认发送？(为了体验更爽，通常直接发)
    const loading = ElLoading.service({
      lock: true,
      text: '正在粘贴发送图片...',
      background: 'rgba(0, 0, 0, 0.7)',
    })

    // 5. 复用之前的上传逻辑
    const res = await uploadFile(imageFile)
    const imgUrl = res.data.data.url

    if (imgUrl) {
      const targetId = chatStore.currentDestId
      if (targetId) {
        // 发送 WebSocket 消息
        socketStore.send({
          type: 'chat',
          to_user_id: targetId,
          content: imgUrl,
        })

        // 本地展示
        chatStore.addMessage({
          sender_id: userStore.userInfo?.id || 0,
          receiver_id: targetId,
          content: imgUrl,
          created_at: dayjs().format('HH:mm'),
          is_self: true,
        })
      }
      ElMessage.success('截图发送成功')
    }

    loading.close()
  } catch (e) {
    console.error('粘贴发送失败', e)
    ElMessage.error('图片粘贴失败')
  }
}

// 初始化
onMounted(async () => {
  await chatStore.loadContacts()
  checkRouteParam()
})

// [新增] 离开页面时，清空当前选中的聊天对象
onUnmounted(() => {
  // 传入 0 或 null 来清空，这样 Socket 就会知道你现在"没在聊天"
  chatStore.selectContact(0)
})

// 监听路由参数变化
watch(
  () => route.query.targetId,
  () => {
    checkRouteParam()
  },
)

const checkRouteParam = () => {
  const targetId = route.query.targetId
  if (targetId) {
    const id = Number(targetId)
    if (chatStore.contacts.length > 0) {
      handleSelect(id)
    } else {
      const unwatch = watch(
        () => chatStore.contacts,
        (newVal) => {
          if (newVal.length > 0) {
            handleSelect(id)
            unwatch()
          }
        },
      )
    }
  }
}

const handleSelect = (id: number) => {
  chatStore.selectContact(id)
}

const scrollToBottom = () => {
  nextTick(() => {
    if (msgContainer.value) {
      msgContainer.value.scrollTop = msgContainer.value.scrollHeight
    }
  })
}

watch(() => currentMessages.value.length, scrollToBottom)

const fireConfetti = () => {
  const duration = 2 * 1000
  const animationEnd = Date.now() + duration
  const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 9999 }

  const randomInRange = (min: number, max: number) => {
    return Math.random() * (max - min) + min
  }

  const interval: any = setInterval(function () {
    const timeLeft = animationEnd - Date.now()

    if (timeLeft <= 0) {
      return clearInterval(interval)
    }

    const particleCount = 50 * (timeLeft / duration)
    confetti({
      ...defaults,
      particleCount,
      origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 },
    })
    confetti({
      ...defaults,
      particleCount,
      origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 },
    })
  }, 250)
}

// 发送普通文本
const handleSend = () => {
  const content = inputContent.value.trim()
  const targetId = chatStore.currentDestId

  if (!content || !targetId) return

  if (['放假', '周六', '周末', 'happy', '🎉'].some((key) => content.includes(key))) {
    fireConfetti()
  }

  socketStore.send({
    type: 'chat',
    to_user_id: targetId,
    content: content,
  })

  chatStore.addMessage({
    sender_id: userStore.userInfo?.id || 0,
    receiver_id: targetId,
    content: content,
    created_at: dayjs().format('HH:mm'),
    is_self: true,
  })

  inputContent.value = ''
}

const formatTime = (timeStr?: string) => {
  if (!timeStr) return ''
  return timeStr.substring(0, 16).replace('T', ' ')
}
</script>
