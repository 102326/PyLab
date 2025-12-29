<template>
  <header class="bg-white border-b border-gray-100 sticky top-0 z-40">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16 items-center">
        <div class="flex items-center cursor-pointer" @click="router.push('/')">
          <div class="h-8 w-8 bg-indigo-600 rounded-lg flex items-center justify-center mr-2">
            <span class="text-white font-bold">P</span>
          </div>
          <span class="text-xl font-bold text-gray-900 tracking-tight">PyLab</span>
        </div>

        <nav class="hidden md:flex space-x-8">
          <router-link to="/" class="nav-item" active-class="text-indigo-600 font-bold"
            >首页</router-link
          >
          <router-link to="/courses" class="nav-item" active-class="text-indigo-600 font-bold"
            >课程</router-link
          >
          <router-link to="/chat" class="nav-item" active-class="text-indigo-600 font-bold"
            >AI 实验室</router-link
          >
        </nav>

        <div class="flex items-center space-x-4">
          <template v-if="userStore.token">
            <el-button
              v-if="userStore.isTeacher"
              type="primary"
              size="small"
              plain
              @click="router.push('/teacher/upload')"
            >
              发布课程
            </el-button>

            <div
              class="h-9 w-9 rounded-full bg-gray-200 cursor-pointer overflow-hidden border border-gray-200 hover:ring-2 hover:ring-indigo-100 transition-all"
              @click="router.push('/user')"
            >
              <img
                v-if="userStore.userInfo.avatar"
                :src="userStore.userInfo.avatar"
                class="w-full h-full object-cover"
              />
              <div
                v-else
                class="w-full h-full flex items-center justify-center text-gray-500 text-xs"
              >
                {{ userStore.userInfo.nickname?.[0] || 'U' }}
              </div>
            </div>
          </template>

          <template v-else>
            <el-button text @click="router.push('/login')">登录</el-button>
            <el-button type="primary" @click="router.push('/register')">注册</el-button>
          </template>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
</script>

<style scoped>
.nav-item {
  @apply text-gray-500 hover:text-gray-900 transition-colors text-sm font-medium;
}
</style>
