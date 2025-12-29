<template>
  <div class="min-h-screen bg-gray-50">
    <div class="bg-indigo-600 py-16 px-4 sm:px-6 lg:px-8">
      <div class="max-w-7xl mx-auto text-center">
        <h1 class="text-4xl font-extrabold text-white sm:text-5xl md:text-6xl tracking-tight">
          PyLab 知识工场
        </h1>
        <p class="mt-4 max-w-2xl mx-auto text-xl text-indigo-100">
          发现前沿技术，与 AI 助教共同进步
        </p>

        <div class="mt-8 max-w-xl mx-auto">
          <div class="relative rounded-md shadow-sm">
            <input
              v-model="query.keyword"
              @keyup.enter="handleSearch"
              type="text"
              class="block w-full rounded-full border-0 py-4 pl-6 pr-12 text-gray-900 ring-1 ring-inset ring-white/20 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-white sm:text-sm sm:leading-6 shadow-lg"
              placeholder="搜索感兴趣的课程 (支持 AI 语义搜索)..."
            />
            <div
              class="absolute inset-y-0 right-0 flex items-center pr-4 cursor-pointer"
              @click="handleSearch"
            >
              <el-icon class="text-indigo-600 text-xl font-bold"><Search /></el-icon>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
      <div
        v-if="loading"
        class="grid grid-cols-1 gap-y-10 gap-x-6 sm:grid-cols-2 lg:grid-cols-4 xl:gap-x-8"
      >
        <div v-for="n in 8" :key="n" class="bg-white rounded-2xl shadow p-4 animate-pulse">
          <div class="h-40 bg-gray-200 rounded-xl mb-4"></div>
          <div class="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div class="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>

      <div v-else>
        <div
          v-if="courseList.length > 0"
          class="grid grid-cols-1 gap-y-10 gap-x-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 xl:gap-x-8"
        >
          <div
            v-for="course in courseList"
            :key="course.id"
            class="group relative bg-white rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden cursor-pointer border border-gray-100"
            @click="router.push(`/course/${course.id}`)"
          >
            <div
              class="aspect-w-16 aspect-h-9 w-full overflow-hidden bg-gray-200 relative group-hover:opacity-90 transition-opacity"
            >
              <img
                :src="course.cover || 'https://via.placeholder.com/640x360?text=No+Cover'"
                class="h-48 w-full object-cover object-center transform group-hover:scale-105 transition-transform duration-500"
              />
              <div
                class="absolute top-2 right-2 bg-black/50 backdrop-blur-sm text-white text-xs px-2 py-1 rounded-md"
              >
                {{ course.price > 0 ? `¥${course.price}` : '免费' }}
              </div>
            </div>

            <div class="p-4">
              <h3
                class="text-lg font-bold text-gray-900 truncate mb-1 group-hover:text-indigo-600 transition-colors"
              >
                {{ course.title }}
              </h3>
              <p class="text-sm text-gray-500 line-clamp-2 h-10 mb-3">
                {{ course.desc || '暂无简介' }}
              </p>

              <div class="flex items-center justify-between mt-4 pt-3 border-t border-gray-50">
                <div class="flex items-center">
                  <div
                    class="h-6 w-6 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-xs font-bold"
                  >
                    {{ course.teacher_name.charAt(0) }}
                  </div>
                  <span class="ml-2 text-xs text-gray-500">{{ course.teacher_name }}</span>
                </div>
                <span class="text-xs text-gray-400">刚刚更新</span>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="text-center py-20">
          <el-empty description="暂无相关课程，试试其他关键词？" />
        </div>

        <div v-if="total > query.size" class="mt-12 flex justify-center">
          <el-pagination
            background
            layout="prev, pager, next"
            :total="total"
            :page-size="query.size"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { CourseApi, type CourseListRes } from '@/api/course'

const router = useRouter()
const loading = ref(true)
const courseList = ref<CourseListRes['items']>([])
const total = ref(0)

const query = reactive({
  page: 1,
  size: 12,
  keyword: '',
})

const fetchCourses = async () => {
  loading.value = true
  try {
    const data = await CourseApi.getCourses(query)
    courseList.value = data.items
    total.value = data.total
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  query.page = 1
  fetchCourses()
}

const handlePageChange = (page: number) => {
  query.page = page
  fetchCourses()
}

onMounted(() => {
  fetchCourses()
})
</script>
