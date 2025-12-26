import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { ChatApi } from '@/api/chat'
import type { ChatContact, ChatMessage } from '@/model/chat'
import { useUserStore } from './user'

export const useChatStore = defineStore('chat', () => {
  // 联系人列表
  const contacts = ref<ChatContact[]>([])

  // 聊天记录缓存：key 是对方的 userId
  const messages = reactive<Record<number, ChatMessage[]>>({})

  // 当前正在聊天的对象 ID
  const currentDestId = ref<number | null>(null)

  // 初始化：拉取联系人
  async function loadContacts() {
    try {
      const list = await ChatApi.getContacts()
      // 直接使用后端返回的数据 (包含未读数、最后一条消息)
      contacts.value = list
    } catch (e) {
      console.error('加载联系人失败', e)
    }
  }

  // 选中某人进行聊天
  async function selectContact(targetId: number) {
    currentDestId.value = targetId

    // 1. 清除该人的未读数 (UI层面)
    const contact = contacts.value.find((c) => c.id === targetId)
    if (contact) contact.unread_count = 0

    // 2. 如果内存里没有记录，去后端拉取历史记录
    if (!messages[targetId]) {
      try {
        const history = await ChatApi.getHistory(targetId)
        const userStore = useUserStore()
        const myId = userStore.userInfo?.id

        messages[targetId] = history.map((m) => ({
          ...m,
          is_self: m.sender_id === myId,
        }))
      } catch (e) {
        console.error('加载历史记录失败', e)
        messages[targetId] = []
      }
    }
  }

  // 核心：接收/发送一条新消息
  function addMessage(msg: ChatMessage) {
    const userStore = useUserStore()
    const myId = userStore.userInfo?.id

    // 判断会话对象
    const sessionId = msg.sender_id === myId ? msg.receiver_id : msg.sender_id

    // 1. 存入消息列表
    if (!messages[sessionId]) {
      messages[sessionId] = []
    }

    const processedMsg = { ...msg, is_self: msg.sender_id === myId }
    messages[sessionId].push(processedMsg)

    // 2. 更新联系人列表 (把这个人顶到最前面，更新最后一条消息)
    const contactIndex = contacts.value.findIndex((c) => c.id === sessionId)
    if (contactIndex !== -1) {
      // 使用 ! 断言，因为我们刚判断了 index !== -1
      const contact = contacts.value[contactIndex]!

      contact.last_msg = msg.content
      contact.last_time = msg.created_at

      // 如果不是自己发的，且没在看，未读数+1
      if (currentDestId.value !== sessionId && msg.sender_id !== myId) {
        contact.unread_count = (contact.unread_count || 0) + 1
      }

      // 移到数组第一位 (置顶)
      contacts.value.splice(contactIndex, 1)
      contacts.value.unshift(contact)
    } else {
      // 如果是新联系人，重新拉取列表
      loadContacts()
    }
  }

  return {
    contacts,
    messages,
    currentDestId,
    loadContacts,
    selectContact,
    addMessage,
  }
})
