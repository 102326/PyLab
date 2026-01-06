<template>
  <header class="bg-white border-b border-gray-100 sticky top-0 z-40 shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16 items-center">
        <div class="flex items-center cursor-pointer gap-2" @click="router.push('/')">
          <div class="h-8 w-8 bg-indigo-600 rounded-lg flex items-center justify-center shadow-md">
            <span class="text-white font-bold text-lg">P</span>
          </div>
          <span class="text-xl font-bold text-gray-900 tracking-tight">PyLab</span>
        </div>

        <nav class="hidden md:flex space-x-8">
          <router-link
            to="/"
            class="text-gray-500 hover:text-indigo-600 transition-colors text-sm font-medium px-1 py-1"
            active-class="!text-indigo-600 font-bold border-b-2 border-indigo-600"
          >
            首页
          </router-link>

          <router-link
            to="/courses"
            class="text-gray-500 hover:text-indigo-600 transition-colors text-sm font-medium px-1 py-1"
            active-class="!text-indigo-600 font-bold border-b-2 border-indigo-600"
          >
            课程大厅
          </router-link>

          <router-link
            to="/chat"
            class="text-gray-500 hover:text-indigo-600 transition-colors text-sm font-medium px-1 py-1 flex items-center gap-1"
            active-class="!text-indigo-600 font-bold border-b-2 border-indigo-600"
          >
            <el-icon><MagicStick /></el-icon>
            AI 实验室
          </router-link>
        </nav>

        <div class="flex items-center space-x-4">
          <template v-if="!userStore.token">
            <el-button text @click="router.push('/login')">登录</el-button>
            <el-button type="primary" class="!rounded-lg" @click="router.push('/login')"
              >注册</el-button
            >
          </template>

          <template v-else>
            <el-button
              v-if="userStore.userInfo?.role === 1"
              type="primary"
              size="small"
              plain
              icon="Upload"
              class="!rounded-full"
              @click="router.push('/teacher/upload')"
            >
              发布课程
            </el-button>

            <div
              class="h-9 w-9 rounded-full bg-gray-100 cursor-pointer overflow-hidden border border-gray-200 hover:ring-2 hover:ring-indigo-100 transition-all flex items-center justify-center"
              @click="router.push('/user')"
              title="个人中心"
            >
              <img
                v-if="userStore.userInfo?.avatar"
                :src="userStore.userInfo.avatar"
                class="w-full h-full object-cover"
              />
              <span v-else class="text-xs font-bold text-gray-500">
                {{ userStore.userInfo?.nickname?.[0]?.toUpperCase() || 'U' }}
              </span>
            </div>
          </template>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
// [新增] 引入 MagicStick 图标
import { MagicStick } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
</script>
