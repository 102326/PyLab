<template>
  <div class="flex h-screen bg-gray-900 text-white overflow-hidden">
    <div class="w-80 flex flex-col border-r border-gray-800 bg-gray-900">
      <div
        class="h-16 flex items-center px-4 border-b border-gray-800 hover:bg-gray-800 transition-colors cursor-pointer"
        @click="router.push(`/course/${route.params.id}`)"
      >
        <el-icon class="mr-2"><ArrowLeft /></el-icon>
        <span class="font-bold truncate">{{ courseTitle || '返回课程详情' }}</span>
      </div>

      <div class="flex-1 overflow-y-auto custom-scrollbar">
        <div v-for="(chapter, cIndex) in chapters" :key="chapter.id">
          <div
            class="px-4 py-3 bg-gray-800/50 text-gray-400 text-xs font-bold uppercase tracking-wider sticky top-0 backdrop-blur-sm z-10"
          >
            {{ chapter.title }}
          </div>

          <div
            v-for="(lesson, lIndex) in chapter.lessons"
            :key="lesson.id"
            class="px-4 py-3 cursor-pointer transition-all border-l-4 hover:bg-gray-800 flex items-center justify-between group"
            :class="
              currentLesson?.id === lesson.id
                ? 'border-indigo-500 bg-gray-800 text-indigo-400'
                : 'border-transparent text-gray-300'
            "
            @click="playLesson(lesson)"
          >
            <div class="flex items-center gap-3 overflow-hidden">
              <el-icon :class="currentLesson?.id === lesson.id ? 'animate-pulse' : ''">
                <VideoPlay v-if="lesson.type === 'video'" />
                <EditPen v-else />
              </el-icon>
              <span class="truncate text-sm">{{ lIndex + 1 }}. {{ lesson.title }}</span>
            </div>

            <div
              v-if="currentLesson?.id === lesson.id"
              class="text-xs font-bold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400"
            >
              进行中
            </div>
          </div>
        </div>

        <div v-if="chapters.length === 0 && !loading" class="p-8 text-center text-gray-500 text-sm">
          暂无章节内容
        </div>
      </div>
    </div>

    <div class="flex-1 flex flex-col relative bg-black">
      <div v-if="currentLesson" class="flex-1 h-full relative group">
        <video
          v-if="currentLesson.type === 'video' && videoUrl"
          :src="videoUrl"
          controls
          autoplay
          class="w-full h-full max-h-screen outline-none"
          controlsList="nodownload"
          @error="handleVideoError"
        >
          您的浏览器不支持 Video 标签。
        </video>

        <ProblemPlayer
          v-else-if="currentLesson.type === 'problem' && currentLesson.problem_id"
          :lesson-id="currentLesson.id"
          :problem-id="currentLesson.problem_id"
        />

        <div v-else class="flex flex-col items-center justify-center h-full text-gray-500">
          <el-icon class="text-4xl mb-4 text-yellow-600"><Warning /></el-icon>
          <p class="text-lg font-medium text-gray-400">暂无资源</p>
          <p class="text-sm mt-2 text-gray-600">该课时未关联视频或题目</p>
        </div>
      </div>

      <div v-else class="flex-1 flex items-center justify-center text-gray-500">
        <div v-if="loading" class="flex flex-col items-center">
          <el-icon class="is-loading text-4xl mb-4"><Loading /></el-icon>
          <p>正在加载课程资源...</p>
        </div>
        <p v-else class="flex flex-col items-center gap-2">
          <el-icon class="text-3xl"><VideoPlay /></el-icon>
          <span>请从左侧选择一个课时开始学习</span>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { CourseApi, type Chapter, type Lesson } from '@/api/course'
// 引入图标
import { ArrowLeft, VideoPlay, EditPen, Loading, Warning } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
// [核心] 引入刚才写的判题组件
import ProblemPlayer from './components/ProblemPlayer.vue'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const courseTitle = ref('')
const chapters = ref<Chapter[]>([])
const currentLesson = ref<Lesson | null>(null)
const videoUrl = ref('')

// 获取课程目录树
const fetchTree = async () => {
  const courseId = Number(route.params.id)
  if (!courseId) return

  try {
    // 1. 获取课程基本信息 (为了显示标题)
    const detail = await CourseApi.getCourseDetail(courseId)
    courseTitle.value = detail.info.title

    // 2. 验证权限 (简单前端验证)
    if (!detail.info.is_joined) {
      ElMessage.warning('请先加入课程')
      router.replace(`/course/${courseId}`)
      return
    }

    // 3. 获取章节目录 (包含 lessons)
    // 请确保 api/course.ts 里已经添加了 getCourseChapters 方法
    const res = await CourseApi.getCourseChapters(courseId)
    chapters.value = res || []

    // 4. 自动播放第一个课时 (如果是重新进来，最好能跳到上次进度，这里先默认第一节)
    if (chapters.value.length > 0 && chapters.value[0].lessons.length > 0) {
      playLesson(chapters.value[0].lessons[0])
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('加载课程失败')
  } finally {
    loading.value = false
  }
}

// 切换课时
const playLesson = (lesson: Lesson) => {
  currentLesson.value = lesson

  if (lesson.type === 'video') {
    // 处理视频逻辑
    if (lesson.video && lesson.video.play_url) {
      videoUrl.value = lesson.video.play_url
    } else {
      videoUrl.value = '' // 清空 URL 避免播放上一个
      if (!loading.value) ElMessage.warning('该课时暂无视频资源')
    }
  } else if (lesson.type === 'problem') {
    // 处理题目逻辑
    // 实际上 ProblemPlayer 组件会根据 problem_id 自动去加载题目
    // 我们只需要把 currentLesson 切换过去，v-if 就会负责渲染 ProblemPlayer
    if (!lesson.problem_id) {
      ElMessage.warning('该练习未关联题目 ID')
    }
  }
}

const handleVideoError = () => {
  ElMessage.error('视频加载失败，请检查网络或资源链接')
}

onMounted(() => {
  fetchTree()
})
</script>

<style scoped>
/* 自定义滚动条 */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #111827;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #374151;
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #4b5563;
}
</style>
