<template>
  <div class="min-h-screen bg-gray-50 py-10 px-4 sm:px-6 lg:px-8">
    <div class="max-w-5xl mx-auto">
      <div class="mb-8 text-center">
        <h2 class="text-3xl font-extrabold text-gray-900 tracking-tight">发布新课程</h2>
        <p class="mt-2 text-sm text-gray-500">上传视频并填写课程信息，我们将自动为您生成课程主页</p>
      </div>

      <div class="bg-white shadow-xl rounded-2xl overflow-hidden grid grid-cols-1 lg:grid-cols-2">
        <div class="p-8 bg-gray-50/50 border-r border-gray-100 space-y-6">
          <h3 class="text-lg font-bold text-gray-800 flex items-center">
            <el-icon class="mr-2 text-blue-500"><Document /></el-icon> 课程基本信息
          </h3>

          <div>
            <label class="block text-sm font-bold text-gray-700 mb-2">课程标题</label>
            <el-input v-model="form.title" placeholder="例如：Vue3 全栈开发实战" size="large" />
          </div>

          <div>
            <label class="block text-sm font-bold text-gray-700 mb-2">课程简介</label>
            <el-input
              v-model="form.desc"
              type="textarea"
              :rows="4"
              placeholder="简单介绍一下这门课程的内容和目标人群..."
            />
          </div>

          <div>
            <label class="block text-sm font-bold text-gray-700 mb-2">课程价格 (元)</label>
            <el-input-number
              v-model="form.price"
              :min="0"
              :precision="2"
              :step="1"
              size="large"
              class="w-full"
            />
            <p class="text-xs text-gray-400 mt-1">设为 0 则为免费课程</p>
          </div>

          <div>
            <label class="block text-sm font-bold text-gray-700 mb-2">课程封面</label>
            <div
              class="relative w-full h-48 border-2 border-dashed border-gray-300 rounded-xl hover:border-blue-500 transition-colors cursor-pointer bg-white group overflow-hidden"
              @click="triggerCoverSelect"
            >
              <img v-if="coverPreview" :src="coverPreview" class="w-full h-full object-cover" />

              <div
                v-else
                class="absolute inset-0 flex flex-col items-center justify-center text-gray-400"
              >
                <el-icon class="text-4xl mb-2 group-hover:text-blue-500 transition-colors"
                  ><Picture
                /></el-icon>
                <span class="text-sm">点击上传封面图</span>
              </div>

              <div
                v-if="coverPreview"
                class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
              >
                <span class="text-white font-medium">更换封面</span>
              </div>
            </div>
            <input
              type="file"
              ref="coverInputRef"
              class="hidden"
              accept="image/*"
              @change="handleCoverSelected"
            />
          </div>
        </div>

        <div class="p-8 space-y-8 flex flex-col">
          <h3 class="text-lg font-bold text-gray-800 flex items-center">
            <el-icon class="mr-2 text-purple-500"><VideoPlay /></el-icon> 课程视频资源
          </h3>

          <div
            class="flex-1 border-2 border-dashed border-gray-300 rounded-xl flex flex-col items-center justify-center p-6 relative hover:border-purple-500 transition-colors cursor-pointer bg-white"
            :class="{ 'border-purple-500 bg-purple-50': videoFile }"
            @click="triggerVideoSelect"
          >
            <div v-if="!videoFile" class="text-center space-y-3">
              <div
                class="w-16 h-16 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center mx-auto"
              >
                <el-icon class="text-3xl"><UploadFilled /></el-icon>
              </div>
              <div>
                <p class="text-gray-900 font-medium">点击选择视频文件</p>
                <p class="text-gray-400 text-xs mt-1">支持 MP4, MOV (Max 1GB)</p>
              </div>
            </div>

            <div v-else class="text-center w-full">
              <el-icon class="text-5xl text-purple-600 mb-3"><VideoCameraFilled /></el-icon>
              <p class="font-bold text-gray-800 truncate px-4">{{ videoFile.name }}</p>
              <p class="text-sm text-gray-500 mb-4">
                {{ (videoFile.size / 1024 / 1024).toFixed(1) }} MB
              </p>
              <el-button type="primary" link @click.stop="triggerVideoSelect">更换视频</el-button>
            </div>

            <input
              type="file"
              ref="videoInputRef"
              class="hidden"
              accept="video/*"
              @change="handleVideoSelected"
            />
          </div>

          <div v-if="uploadState.status !== 'idle'" class="space-y-4">
            <div v-if="coverFile" class="space-y-1">
              <div class="flex justify-between text-xs text-gray-500">
                <span>封面上传</span>
                <span>{{ uploadState.coverPercent }}%</span>
              </div>
              <el-progress
                :percentage="uploadState.coverPercent"
                :show-text="false"
                status="success"
              />
            </div>

            <div class="space-y-1">
              <div class="flex justify-between text-xs text-gray-500">
                <span>视频上传</span>
                <span>{{ uploadState.videoPercent }}%</span>
              </div>
              <el-progress
                :percentage="uploadState.videoPercent"
                :show-text="false"
                :status="uploadState.status === 'error' ? 'exception' : ''"
              />
            </div>

            <p class="text-center text-sm font-medium" :class="statusColor">
              {{ statusText }}
            </p>
          </div>

          <div class="pt-4">
            <el-button
              type="primary"
              size="large"
              class="w-full !rounded-xl !h-12 !text-lg !font-bold shadow-lg shadow-blue-500/30"
              :loading="uploadState.status === 'uploading'"
              :disabled="!isReady"
              @click="startPublish"
            >
              {{ uploadState.status === 'uploading' ? '正在发布中...' : '立即发布课程' }}
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Document,
  Picture,
  UploadFilled,
  VideoPlay,
  VideoCameraFilled,
} from '@element-plus/icons-vue'
import * as qiniu from 'qiniu-js'
import { MediaApi } from '@/api/media'
import { CourseApi } from '@/api/course'

const router = useRouter()

// === 表单数据 ===
const form = reactive({
  title: '',
  desc: '',
  price: 0,
})

const coverFile = ref<File | null>(null)
const coverPreview = ref('')
const videoFile = ref<File | null>(null)

// === 上传状态管理 ===
const uploadState = reactive({
  status: 'idle' as 'idle' | 'uploading' | 'processing' | 'success' | 'error',
  coverPercent: 0,
  videoPercent: 0,
})

const coverInputRef = ref<HTMLInputElement>()
const videoInputRef = ref<HTMLInputElement>()

// === 计算属性 ===
const isReady = computed(() => {
  return form.title && videoFile.value
})

const statusText = computed(() => {
  switch (uploadState.status) {
    case 'uploading':
      return '正在上传资源到云端...'
    case 'processing':
      return '资源上传完成，正在创建课程...'
    case 'success':
      return '发布成功！正在跳转...'
    case 'error':
      return '发布失败，请重试'
    default:
      return ''
  }
})

const statusColor = computed(() => {
  return uploadState.status === 'error' ? 'text-red-500' : 'text-blue-600'
})

// === 文件选择逻辑 ===
const triggerCoverSelect = () => coverInputRef.value?.click()
const triggerVideoSelect = () => videoInputRef.value?.click()

const handleCoverSelected = (e: Event) => {
  const files = (e.target as HTMLInputElement).files
  if (files?.[0]) {
    coverFile.value = files[0]
    coverPreview.value = URL.createObjectURL(files[0]) // 本地预览
    uploadState.coverPercent = 0
  }
}

const handleVideoSelected = (e: Event) => {
  const files = (e.target as HTMLInputElement).files
  if (files?.[0]) {
    videoFile.value = files[0]
    // 如果还没填标题，自动用文件名当标题
    if (!form.title) form.title = files[0].name.replace(/\.[^/.]+$/, '')
    uploadState.videoPercent = 0
  }
}

// === 核心：七牛云上传封装 ===
// 返回 Promise<{ key, hash, ... }>
const uploadToQiniu = async (
  file: File,
  type: 'video' | 'image',
  onProgress: (p: number) => void,
) => {
  const { token, domain } = await MediaApi.getUploadToken()
  const key = `${type}s/${Date.now()}_${file.name}` // videos/... 或 images/...

  return new Promise<any>((resolve, reject) => {
    // region: qiniu.region.z1 表示华北区，如果你是其他区请修改
    const observable = qiniu.upload(
      file,
      key,
      token,
      { useCdnDomain: true, region: qiniu.region.z1 },
      {},
    )
    observable.subscribe({
      next: (res) => onProgress(Math.floor(res.total.percent)),
      error: (err) => reject(err),
      complete: (res) => resolve({ ...res, domain }), // 把 domain 也带回去方便拼 URL
    })
  })
}

// === 核心：发布流程 ===
const startPublish = async () => {
  if (!videoFile.value || !form.title) return

  uploadState.status = 'uploading'

  try {
    // 1. 上传封面 (如果有)
    let coverUrl = ''
    if (coverFile.value) {
      const coverRes = await uploadToQiniu(
        coverFile.value,
        'image',
        (p) => (uploadState.coverPercent = p),
      )
      coverUrl = `${coverRes.domain}/${coverRes.key}`
      // 补全协议头
      if (!coverUrl.startsWith('http')) coverUrl = 'http://' + coverUrl
    }

    // 2. 上传视频 (必须)
    const videoRes = await uploadToQiniu(
      videoFile.value,
      'video',
      (p) => (uploadState.videoPercent = p),
    )

    uploadState.status = 'processing'

    // 3. 后端：创建视频资源
    const videoData = await MediaApi.createVideo({
      title: form.title, // 视频名暂时和课程名一样
      file_key: videoRes.key,
      file_hash: videoRes.hash,
      file_size: videoRes.fsize, // 注意：七牛返回的是 fsize
      duration: 0,
    })
    const videoId = videoData.id

    // 4. 后端：创建课程
    const course = await CourseApi.createCourse({
      title: form.title,
      desc: form.desc,
      price: form.price,
      cover: coverUrl,
    })

    // 5. 后端：创建默认章节
    const chapter = await CourseApi.createChapter(course.id, {
      title: '第一章：课程导论',
      rank: 1,
    })

    // 6. 后端：创建课时并挂载视频
    await CourseApi.createLesson(course.id, chapter.id, {
      title: form.title, // 课时名也先用课程名
      type: 'video',
      rank: 1,
      video_id: videoId,
    })

    // 7. 完成
    uploadState.status = 'success'
    ElMessage.success('课程发布成功！AI 正在后台为您构建知识库...')

    // 延迟跳转到首页或课程列表
    setTimeout(() => {
      router.push('/')
    }, 1500)
  } catch (error: any) {
    console.error(error)
    uploadState.status = 'error'
    ElMessage.error(error.message || '发布失败')
  }
}
</script>
