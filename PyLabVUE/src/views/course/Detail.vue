<template>
  <div class="min-h-screen bg-gray-50 pb-20">
    <div v-if="loading" class="max-w-7xl mx-auto py-12 px-4 space-y-8 animate-pulse">
      <div class="h-64 bg-gray-200 rounded-2xl"></div>
      <div class="h-8 bg-gray-200 rounded w-1/3"></div>
    </div>

    <div v-else-if="course" class="animate-fade-in">
      <div class="bg-gray-900 text-white relative overflow-hidden">
        <div
          class="absolute inset-0 opacity-20 bg-gradient-to-r from-indigo-900 to-purple-900"
        ></div>
        <div
          class="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8 relative z-10 flex flex-col md:flex-row gap-8"
        >
          <div
            class="w-full md:w-1/2 lg:w-5/12 aspect-video bg-gray-800 rounded-xl overflow-hidden shadow-2xl relative group"
          >
            <img
              :src="course.cover"
              class="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity"
            />
            <div
              class="absolute inset-0 flex items-center justify-center cursor-pointer"
              @click="handleMainAction"
            >
              <div
                class="w-16 h-16 bg-white/20 backdrop-blur rounded-full flex items-center justify-center hover:scale-110 transition-transform"
              >
                <el-icon class="text-3xl text-white"><VideoPlay /></el-icon>
              </div>
            </div>
          </div>

          <div class="flex-1 space-y-4">
            <div class="flex items-center space-x-2 text-indigo-300 text-sm font-medium">
              <span class="bg-indigo-500/20 px-2 py-1 rounded">视频课程</span>
              <span>•</span>
              <span>{{ course.view_count }} 次浏览</span>
            </div>

            <h1 class="text-3xl md:text-4xl font-bold leading-tight">{{ course.title }}</h1>

            <p class="text-gray-300 text-lg leading-relaxed line-clamp-3">
              {{ course.desc }}
            </p>

            <div class="pt-6 flex items-center gap-4">
              <el-button
                type="primary"
                size="large"
                class="!px-8 !text-lg !font-bold !rounded-full shadow-lg shadow-indigo-500/30 w-48 transition-all"
                :loading="joining"
                @click="handleMainAction"
              >
                {{ actionButtonText }}
              </el-button>

              <div v-if="!course.is_joined" class="text-2xl font-bold text-yellow-400">
                {{ course.price > 0 ? `¥${course.price}` : '免费' }}
              </div>
              <div v-else class="text-green-400 font-bold flex items-center">
                <el-icon class="mr-1"><Select /></el-icon> 已加入学习
              </div>
            </div>

            <div class="flex items-center pt-4">
              <div
                class="h-8 w-8 rounded-full bg-gray-700 flex items-center justify-center text-xs font-bold mr-3"
              >
                {{ course.teacher_name?.charAt(0) }}
              </div>
              <span class="text-gray-400">讲师：{{ course.teacher_name }}</span>
            </div>
          </div>
        </div>
      </div>

      <div
        class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 grid grid-cols-1 lg:grid-cols-3 gap-12"
      >
        <div class="lg:col-span-2 space-y-8">
          <div class="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
            <h2 class="text-xl font-bold text-gray-900 mb-6 flex items-center">
              <el-icon class="mr-2 text-indigo-600"><Document /></el-icon> 课程介绍
            </h2>
            <div class="prose max-w-none text-gray-600 whitespace-pre-wrap">
              {{ course.desc || '暂无详细介绍' }}
            </div>
          </div>
        </div>

        <div class="space-y-6">
          <h3 class="text-lg font-bold text-gray-800 flex items-center">
            <el-icon class="mr-2 text-orange-500"><Star /></el-icon> 猜你喜欢
          </h3>

          <div v-if="relatedCourses.length > 0" class="space-y-4">
            <div
              v-for="rc in relatedCourses"
              :key="rc.id"
              class="bg-white rounded-xl p-3 flex gap-3 shadow-sm hover:shadow-md transition-all cursor-pointer border border-gray-100 group"
              @click="router.push(`/course/${rc.id}`)"
            >
              <div class="w-24 h-16 rounded-lg bg-gray-200 overflow-hidden shrink-0">
                <img
                  :src="rc.cover"
                  class="w-full h-full object-cover group-hover:scale-105 transition-transform"
                />
              </div>
              <div class="flex-1 min-w-0 flex flex-col justify-center">
                <h4
                  class="text-sm font-bold text-gray-900 truncate mb-1 group-hover:text-indigo-600"
                >
                  {{ rc.title }}
                </h4>
                <div class="flex justify-between items-center text-xs text-gray-500">
                  <span v-if="rc.price === 0" class="text-green-600">免费</span>
                  <span v-else>¥{{ rc.price }}</span>
                  <span class="flex items-center"
                    ><el-icon class="mr-1"><View /></el-icon> {{ rc.view_count }}</span
                  >
                </div>
              </div>
            </div>
          </div>

          <div v-else class="text-gray-400 text-sm text-center py-4">暂无相关推荐</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { VideoPlay, Document, Star, View, Select } from '@element-plus/icons-vue'
import { CourseApi, type Course } from '@/api/course'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loading = ref(true)
const joining = ref(false) // 加入按钮的 loading 状态
const course = ref<Course | null>(null)
const relatedCourses = ref<Course[]>([])

// 动态计算按钮文字
const actionButtonText = computed(() => {
  if (!userStore.token) return '登录后加入'
  if (course.value?.is_joined) return '继续学习'
  return course.value?.price && course.value.price > 0 ? '立即购买' : '立即加入'
})

// === 核心逻辑：获取详情 ===
const fetchDetail = async (id: number) => {
  loading.value = true
  try {
    const data = await CourseApi.getCourseDetail(id)
    course.value = data.info
    relatedCourses.value = data.related
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

// === 核心逻辑：主按钮点击 ===
const handleMainAction = async () => {
  // 1. 未登录 -> 去登录
  if (!userStore.token) {
    router.push(`/login?redirect=${route.fullPath}`)
    return
  }

  // 2. 已加入 -> 去播放页
  if (course.value?.is_joined) {
    // 假设播放页路由是 /course/:id/learn
    // 目前还没写 Player，先弹个窗
    ElMessage.success('正在跳转播放页...')
    router.push(`/course/${course.value.id}/learn`)
    return
  }

  // 3. 未加入 -> 调用加入接口
  joining.value = true
  try {
    await CourseApi.joinCourse(course.value!.id)
    ElMessage.success('加入成功！')

    // 成功后，手动更新本地状态，不需要刷新页面
    if (course.value) {
      course.value.is_joined = true
    }
  } catch (error: any) {
    ElMessage.error(error.message || '加入失败')
  } finally {
    joining.value = false
  }
}

watch(
  () => route.params.id,
  (newId) => {
    if (newId) fetchDetail(Number(newId))
  },
)

onMounted(() => {
  if (route.params.id) {
    fetchDetail(Number(route.params.id))
  }
})
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.5s ease-out;
}
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
