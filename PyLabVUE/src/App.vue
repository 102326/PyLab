<template>
  <TheHeader />

  <div class="min-h-[calc(100vh-64px)] bg-gray-50">
    <RouterView />
  </div>

  <button
    v-if="showNotifyButton"
    @click="enableNotification"
    class="fixed bottom-32 right-8 z-50 flex items-center gap-2 px-4 py-2 bg-indigo-600/90 backdrop-blur text-white rounded-full shadow-lg hover:bg-indigo-700 transition-all duration-300 animate-bounce cursor-pointer border border-indigo-400"
  >
    <span>🔔</span>
    <span class="text-sm font-medium">开启消息提醒</span>
  </button>

  <el-popover
    v-if="!isChatPage"
    placement="left-end"
    :width="200"
    trigger="hover"
    popper-class="!p-2 !rounded-xl"
  >
    <template #reference>
      <div
        class="fixed bottom-8 right-8 z-50 flex items-center justify-center w-14 h-14 bg-indigo-600 text-white rounded-full shadow-2xl hover:bg-indigo-700 transition-all cursor-pointer hover:scale-110"
      >
        <el-icon class="text-2xl"><Comment /></el-icon>
      </div>
    </template>

    <div class="flex flex-col gap-1">
      <div
        class="flex items-center gap-3 p-3 rounded-lg hover:bg-indigo-50 cursor-pointer transition-colors"
        @click="router.push('/chat/ai')"
      >
        <div
          class="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center"
        >
          <el-icon><MagicStick /></el-icon>
        </div>
        <div class="flex flex-col">
          <span class="text-sm font-bold text-gray-800">AI 助教</span>
          <span class="text-xs text-gray-400">智能问答</span>
        </div>
      </div>

      <div
        class="flex items-center gap-3 p-3 rounded-lg hover:bg-green-50 cursor-pointer transition-colors"
        @click="router.push('/chat/user')"
      >
        <div
          class="w-8 h-8 rounded-full bg-green-100 text-green-600 flex items-center justify-center"
        >
          <el-icon><ChatDotRound /></el-icon>
        </div>
        <div class="flex flex-col">
          <span class="text-sm font-bold text-gray-800">消息中心</span>
          <span class="text-xs text-gray-400">用户沟通</span>
        </div>
      </div>
    </div>
  </el-popover>
</template>

<script setup lang="ts">
import { onMounted, watch, computed } from 'vue'
import { RouterView, useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useSocketStore } from '@/stores/socket'
import { useBrowserNotification } from '@/composables/useBrowserNotification'
import TheHeader from '@/components/layout/TheHeader.vue'
import { Comment, MagicStick, ChatDotRound } from '@element-plus/icons-vue' // [新增图标]

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const socketStore = useSocketStore()

// [修改] 判断是否在聊天页面 (只要路径含 /chat/ 就隐藏)
const isChatPage = computed(() => route.path.includes('/chat/'))

const { permission, requestPermission, sendNotification, subscribeToPush } =
  useBrowserNotification()

const showNotifyButton = computed(() => {
  return permission.value === 'default' && 'Notification' in window
})

const enableNotification = async () => {
  const granted = await requestPermission()
  if (granted) {
    sendNotification('系统通知', { body: '通知已开启！' })
    await subscribeToPush()
  }
}

watch(
  () => socketStore.latestMessage,
  (newMessage) => {
    if (!newMessage) return
    if (newMessage.type === 'chat') {
      sendNotification(`收到新消息`, {
        body: newMessage.content || '您有一条新消息',
        icon: '/favicon.ico',
        tag: 'chat-msg',
      })
    }
  },
  { deep: true },
)

onMounted(() => {
  userStore.initUser()
  if (userStore.token && userStore.userInfo?.id) {
    socketStore.connect()
  }
})

watch(
  () => userStore.token,
  (newToken) => {
    if (newToken) {
      socketStore.connect()
    } else {
      socketStore.disconnect()
    }
  },
)
</script>
