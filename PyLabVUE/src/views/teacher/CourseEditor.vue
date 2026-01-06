<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-1 bg-white rounded-xl shadow-sm p-4 h-fit min-h-[600px]">
        <div class="flex justify-between items-center mb-4 border-b pb-2">
          <h3 class="font-bold text-gray-700">课程目录</h3>
        </div>

        <el-skeleton :rows="5" v-if="loading" />
        <div v-else-if="chapters.length === 0" class="text-center py-10 text-gray-400 text-sm">
          暂无章节
        </div>

        <el-collapse v-else v-model="activeNames">
          <el-collapse-item
            v-for="chapter in chapters"
            :key="chapter.id"
            :name="chapter.id"
            :title="chapter.title"
          >
            <template #title>
              <span class="font-medium truncate w-48">{{ chapter.title }}</span>
            </template>

            <div class="space-y-1">
              <div
                v-for="lesson in chapter.lessons"
                :key="lesson.id"
                class="flex items-center p-2 rounded cursor-pointer hover:bg-gray-100 transition-colors"
                :class="
                  currentLesson?.id === lesson.id ? 'bg-indigo-50 text-indigo-600' : 'text-gray-600'
                "
                @click="handleLessonSelect(lesson)"
              >
                <el-icon class="mr-2">
                  <component :is="lesson.type === 'video' ? 'VideoPlay' : 'Monitor'" />
                </el-icon>
                <span class="truncate text-sm">{{ lesson.title }}</span>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>

      <div class="lg:col-span-2 bg-white rounded-xl shadow-sm p-6 min-h-[600px] flex flex-col">
        <div
          v-if="!currentLesson"
          class="flex-1 flex flex-col items-center justify-center text-gray-400"
        >
          <el-icon class="text-6xl mb-4"><FolderOpened /></el-icon>
          <p>请在左侧选择课时进行编辑</p>
        </div>

        <div v-else class="flex-1 flex flex-col">
          <div class="border-b pb-4 mb-4 flex justify-between items-center">
            <h2 class="text-xl font-bold flex items-center">
              <el-icon class="mr-2 text-indigo-600">
                <component :is="currentLesson.type === 'video' ? 'VideoPlay' : 'Monitor'" />
              </el-icon>
              {{ currentLesson.title }}
            </h2>
            <el-tag>{{ currentLesson.type === 'video' ? '视频课' : '编程练习' }}</el-tag>
          </div>

          <div v-if="currentLesson.type === 'video'" class="space-y-4">
            <div class="aspect-video bg-black rounded-lg overflow-hidden shadow-lg relative group">
              <video
                v-if="currentLesson.video?.file_key"
                controls
                class="w-full h-full"
                :src="getVideoUrl(currentLesson.video.file_key)"
              ></video>
              <div
                v-else
                class="w-full h-full flex items-center justify-center text-gray-500 bg-gray-100"
              >
                <p>暂未绑定视频</p>
              </div>
            </div>

            <div class="bg-blue-50 p-4 rounded-lg border border-blue-100">
              <p class="text-sm text-blue-800 font-bold mb-2">当前绑定资源</p>
              <p v-if="currentLesson.video" class="text-sm">
                文件名: {{ currentLesson.video.title }} <br />
                大小: {{ (currentLesson.video.file_size / 1024 / 1024).toFixed(1) }} MB
              </p>
              <el-button v-else type="primary" size="small">请在左侧点击编辑按钮绑定</el-button>
            </div>
          </div>

          <div v-else-if="currentLesson.type === 'problem'" class="flex-1 flex flex-col">
            <div
              v-if="!problemForm.id && !currentLesson.problem"
              class="flex-1 flex flex-col items-center justify-center space-y-4"
            >
              <el-empty description="当前课时未关联题目" />
              <el-button type="primary" @click="initCreateProblem">创建新题目</el-button>
            </div>

            <div v-else class="space-y-4 flex-1 flex flex-col">
              <el-form label-position="top" class="flex-1 flex flex-col">
                <el-form-item label="题目标题">
                  <el-input v-model="problemForm.title" />
                </el-form-item>

                <div class="grid grid-cols-2 gap-4">
                  <el-form-item label="时间限制(ms)">
                    <el-input-number v-model="problemForm.time_limit" :step="100" />
                  </el-form-item>
                  <el-form-item label="内存限制(MB)">
                    <el-input-number v-model="problemForm.memory_limit" :step="16" />
                  </el-form-item>
                </div>

                <el-form-item label="题目描述 (Markdown)">
                  <el-input
                    v-model="problemForm.content"
                    type="textarea"
                    :rows="6"
                    placeholder="支持 Markdown 格式"
                  />
                </el-form-item>

                <el-form-item label="初始代码模板 (Python)">
                  <el-input
                    v-model="problemForm.init_code"
                    type="textarea"
                    :rows="6"
                    class="font-mono bg-gray-50"
                  />
                </el-form-item>

                <div class="mt-auto pt-4 flex justify-end">
                  <el-button type="primary" @click="saveProblem" :loading="savingProblem"
                    >保存题目内容</el-button
                  >
                </div>
              </el-form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { VideoPlay, Monitor, FolderOpened } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { CourseApi, type Chapter } from '@/api/course'
import { OJApi } from '@/api/oj'

const route = useRoute()
const courseId = Number(route.params.id)

const loading = ref(false)
const chapters = ref<Chapter[]>([])
const activeNames = ref<number[]>([]) // 控制折叠面板
const currentLesson = ref<any>(null)

// OJ 表单
const problemForm = reactive({
  id: 0,
  title: '',
  content: '',
  init_code: 'print("Hello World")',
  time_limit: 1000,
  memory_limit: 128,
})
const savingProblem = ref(false)

// 初始化
const initData = async () => {
  loading.value = true
  try {
    chapters.value = await CourseApi.getCourseChapters(courseId)
    activeNames.value = chapters.value.map((c) => c.id) // 默认全展开
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

// 选中课时
const handleLessonSelect = (lesson: any) => {
  currentLesson.value = lesson
  // 回显 OJ 数据
  if (lesson.type === 'problem' && lesson.problem) {
    problemForm.id = lesson.problem.id
    problemForm.title = lesson.problem.title
    problemForm.content = lesson.problem.content
    problemForm.init_code = lesson.problem.init_code
    problemForm.time_limit = lesson.problem.time_limit
  } else {
    // 重置表单
    problemForm.id = 0
    problemForm.title = lesson.title
    problemForm.content = '### 题目描述\n\n请在此处输入题目描述...'
    problemForm.init_code = '# 在此输入代码模板\n'
  }
}

// === ⚠️ 关键修复：请替换为你真实的七牛云测试域名 ===
const getVideoUrl = (key: string) => {
  // 必须带 http:// 或 https://，例如: 'http://r8q8abc.hn-bkt.clouddn.com'
  const domain = 'http://YOUR_REAL_DOMAIN_HERE.com'
  return `${domain}/${key}`
}

const initCreateProblem = () => {
  problemForm.title = currentLesson.value.title
  problemForm.content = '### 题目描述'
}

const saveProblem = async () => {
  savingProblem.value = true
  try {
    let res
    if (problemForm.id) {
      res = await OJApi.updateProblem(problemForm.id, problemForm)
    } else {
      res = await OJApi.createProblem(problemForm)
      // 绑定到课时
      await CourseApi.updateLesson(currentLesson.value.id, {
        title: currentLesson.value.title,
        type: 'problem',
        rank: currentLesson.value.rank,
        problem_id: res.id,
      })
    }
    ElMessage.success('题目保存成功')
    initData() // 刷新拿到最新的 problem 数据
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    savingProblem.value = false
  }
}

onMounted(() => {
  initData()
})
</script>
