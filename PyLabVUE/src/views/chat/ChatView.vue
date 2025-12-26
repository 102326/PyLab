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
              <p class="text-sm text-gray-500 truncate">{{ contact.last_msg || '暂无消息' }}</p>
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
                  :class="
                    msg.is_self
                      ? 'bg-blue-600 text-white rounded-tr-none'
                      : 'bg-white text-gray-800 border border-gray-200 rounded-tl-none'
                  "
                >
                  {{ msg.content }}
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
            <div class="flex gap-2">
              <el-input
                v-model="inputContent"
                placeholder="请输入消息..."
                @keyup.enter="handleSend"
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
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router' // 引入 useRoute
import { useChatStore } from '@/stores/chat'
import { useSocketStore } from '@/stores/socket'
import { useUserStore } from '@/stores/user'
import { ChatLineRound } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const chatStore = useChatStore()
const socketStore = useSocketStore()
const userStore = useUserStore()
const route = useRoute()

const inputContent = ref('')
const msgContainer = ref<HTMLElement>()

const currentContact = computed(() =>
  chatStore.contacts.find((c) => c.id === chatStore.currentDestId),
)

const currentMessages = computed(() =>
  chatStore.currentDestId ? chatStore.messages[chatStore.currentDestId] || [] : [],
)

// 初始化
onMounted(async () => {
  await chatStore.loadContacts()
  checkRouteParam()
})

// 监听路由参数变化 (解决点击通知跳转后页面不刷新的问题)
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
    // 如果联系人已加载，直接选中
    if (chatStore.contacts.length > 0) {
      handleSelect(id)
    } else {
      // 如果数据还没回来，监听 contacts 变化，一旦有数据就选中
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

const handleSend = () => {
  const content = inputContent.value.trim()
  const targetId = chatStore.currentDestId

  if (!content || !targetId) return

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
