<template>
  <RouterView />
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import { onMounted, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import { useSocketStore } from '@/stores/socket'

const userStore = useUserStore()
const socketStore = useSocketStore()

onMounted(() => {
  // 1. 初始化用户信息
  userStore.initUser()

  // 2. 如果已登录，立刻连接 WS
  if (userStore.token && userStore.userInfo?.id) {
    socketStore.connect()
  }
})

// 3. 监听 Token 变化 (处理登录/登出瞬间)
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
