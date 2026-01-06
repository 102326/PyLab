<template>
  <div class="min-h-screen bg-gray-50 pb-20">
    <div class="bg-indigo-600 py-16 px-4 sm:px-6 lg:px-8 shadow-lg relative overflow-hidden">
      <div class="absolute inset-0 opacity-10 pattern-dots"></div>

      <div class="max-w-7xl mx-auto text-center relative z-10">
        <h1 class="text-4xl font-extrabold text-white sm:text-5xl md:text-6xl tracking-tight mb-4">
          PyLab 知识工场
        </h1>
        <p class="max-w-2xl mx-auto text-xl text-indigo-100 mb-8">
          发现前沿技术，与 AI 助教共同进步
        </p>

        <div class="max-w-xl mx-auto">
          <div class="relative group">
            <input
              v-model="query.keyword"
              @keyup.enter="handleSearch"
              type="text"
              class="block w-full rounded-full border-0 py-4 pl-6 pr-12 text-gray-900 shadow-xl ring-1 ring-inset ring-white/20 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-300 sm:text-lg transition-all"
              placeholder="搜索感兴趣的课程 (支持 AI 语义搜索)..."
            />
            <div
              class="absolute inset-y-0 right-2 flex items-center pr-2 cursor-pointer hover:scale-110 transition-transform"
              @click="handleSearch"
            >
              <div class="bg-indigo-500 p-2 rounded-full text-white shadow-md">
                <el-icon class="text-lg font-bold"><Search /></el-icon>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
      <div class="flex flex-col sm:flex-row justify-between items-center mb-8 gap-4">
        <h2 class="text-2xl font-bold text-gray-800 flex items-center">
          <span class="mr-2">{{ query.keyword ? '🔍' : '📚' }}</span>
          {{ query.keyword ? '搜索结果' : '全部课程' }}
        </h2>

        <div
          v-if="!query.keyword"
          class="bg-white p-1 rounded-lg shadow-sm border border-gray-200 flex"
        >
          <button
            @click="changeSort('new')"
            class="px-4 py-2 rounded-md text-sm font-medium transition-all"
            :class="
              query.sort === 'new'
                ? 'bg-indigo-100 text-indigo-700 shadow-sm'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            "
          >
            最新发布
          </button>
          <button
            @click="changeSort('hot')"
            class="px-4 py-2 rounded-md text-sm font-medium transition-all flex items-center"
            :class="
              query.sort === 'hot'
                ? 'bg-orange-100 text-orange-700 shadow-sm'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            "
          >
            <el-icon class="mr-1"
              ><component :is="query.sort === 'hot' ? 'Fire' : 'Lightning'"
            /></el-icon>
            热门榜单
          </button>
        </div>

        <div v-else>
          <button
            @click="clearSearch"
            class="px-4 py-2 text-sm font-medium text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-md transition-all flex items-center"
          >
            <el-icon class="mr-1"><CircleClose /></el-icon> 清除搜索
          </button>
        </div>
      </div>

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
            class="group relative bg-white rounded-2xl shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 overflow-hidden cursor-pointer border border-gray-100"
            @click="router.push(`/course/${course.id}`)"
          >
            <div class="aspect-w-16 aspect-h-9 w-full overflow-hidden bg-gray-200 relative">
              <img
                :src="course.cover || 'https://via.placeholder.com/640x360?text=No+Cover'"
                class="h-48 w-full object-cover object-center transform group-hover:scale-105 transition-transform duration-500"
              />
              <div
                class="absolute top-2 right-2 bg-black/60 backdrop-blur-md text-white text-xs px-2 py-1 rounded-md font-medium"
              >
                {{ course.price > 0 ? `¥${course.price}` : '免费' }}
              </div>
              <div
                v-if="query.sort === 'hot' && !query.keyword"
                class="absolute bottom-2 left-2 bg-orange-500/90 text-white text-xs px-2 py-1 rounded-md flex items-center"
              >
                <el-icon class="mr-1"><View /></el-icon> {{ course.view_count }}
              </div>
            </div>

            <div class="p-5">
              <h3
                class="text-lg font-bold text-gray-900 truncate mb-2 group-hover:text-indigo-600 transition-colors"
              >
                {{ course.title }}
              </h3>
              <p class="text-sm text-gray-500 line-clamp-2 h-10 mb-4 leading-relaxed">
                {{ course.desc || '暂无简介' }}
              </p>

              <div class="flex items-center justify-between pt-4 border-t border-gray-50">
                <div class="flex items-center">
                  <div
                    class="h-7 w-7 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center text-xs font-bold border border-indigo-100"
                  >
                    {{ course.teacher_name?.charAt(0) || 'T' }}
                  </div>
                  <span class="ml-2 text-xs font-medium text-gray-600 max-w-[80px] truncate">
                    {{ course.teacher_name || '讲师' }}
                  </span>
                </div>
                <span v-if="query.sort !== 'hot'" class="text-xs text-gray-400 flex items-center">
                  <el-icon class="mr-1"><View /></el-icon> {{ course.view_count }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div
          v-else
          class="text-center py-24 bg-white rounded-3xl shadow-sm border border-gray-100 mt-4"
        >
          <el-icon class="text-6xl text-gray-300 mb-4"><Search /></el-icon>
          <p class="text-gray-500 text-lg">
            {{ query.keyword ? '没有找到相关课程，换个词试试？' : '暂时没有课程发布' }}
          </p>
          <button
            v-if="query.keyword"
            @click="clearSearch"
            class="mt-4 text-indigo-600 hover:text-indigo-800 font-medium"
          >
            查看全部课程
          </button>
        </div>

        <div v-if="total > query.size" class="mt-12 flex justify-center">
          <el-pagination
            background
            layout="prev, pager, next"
            :total="total"
            :page-size="query.size"
            :current-page="query.page"
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
// [修改] 引入了 CircleClose 图标
import { Search, View, Fire, Lightning, CircleClose } from '@element-plus/icons-vue'
import { CourseApi, type CourseListRes } from '@/api/course'

const router = useRouter()
const loading = ref(true)
const courseList = ref<CourseListRes['items']>([])
const total = ref(0)

const query = reactive({
  page: 1,
  size: 12,
  keyword: '',
  sort: 'new' as 'new' | 'hot',
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
  // 搜索时重置回第一页
  query.page = 1
  fetchCourses()
}

// [新增] 清除搜索
const clearSearch = () => {
  query.keyword = ''
  query.page = 1
  // 恢复默认排序（可选）
  // query.sort = 'new'
  fetchCourses()
}

const changeSort = (sortType: 'new' | 'hot') => {
  if (query.sort === sortType) return
  query.sort = sortType
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

<style scoped>
.pattern-dots {
  background-image: radial-gradient(#ffffff 1px, transparent 1px);
  background-size: 20px 20px;
}
</style>
