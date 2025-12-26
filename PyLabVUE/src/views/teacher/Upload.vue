<template>
  <div class="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-3xl mx-auto">
      <div class="bg-white shadow sm:rounded-lg overflow-hidden">
        <div class="px-4 py-5 sm:px-6 border-b border-gray-200 bg-gray-50">
          <h3 class="text-lg leading-6 font-medium text-gray-900">发布新课程</h3>
          <p class="mt-1 max-w-2xl text-sm text-gray-500">上传视频资源，分享你的编程知识</p>
        </div>

        <div class="p-6 space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-700">课程标题</label>
            <div class="mt-1">
              <el-input
                v-model="videoTitle"
                placeholder="例如：Python 基础入门 - 第1章"
                size="large"
              />
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700">视频文件</label>
            <div
              class="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md cursor-pointer hover:border-indigo-500 transition-colors relative"
              @click="triggerFileSelect"
            >
              <div v-if="!selectedFile" class="space-y-1 text-center">
                <el-icon class="mx-auto h-12 w-12 text-gray-400 text-4xl"><VideoPlay /></el-icon>
                <div class="flex text-sm text-gray-600 justify-center">
                  <span
                    class="relative bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500"
                  >
                    选择视频文件
                  </span>
                </div>
                <p class="text-xs text-gray-500">支持 MP4, MOV, Max 500MB</p>
              </div>

              <div v-else class="text-center">
                <el-icon class="mx-auto h-10 w-10 text-green-500 text-3xl"
                  ><SuccessFilled
                /></el-icon>
                <p class="mt-2 text-sm text-gray-900 font-medium">{{ selectedFile.name }}</p>
                <p class="text-xs text-gray-500">
                  {{ (selectedFile.size / 1024 / 1024).toFixed(2) }} MB
                </p>
                <el-button link type="primary" @click.stop="triggerFileSelect">更换文件</el-button>
              </div>

              <input
                type="file"
                ref="fileInputRef"
                class="hidden"
                accept="video/*"
                @change="handleFileSelected"
              />
            </div>
          </div>

          <div v-if="uploading || uploadStatus === 'success'" class="animate-fade-in">
            <div class="flex justify-between text-sm text-gray-600 mb-1">
              <span>{{ uploadStatusText }}</span>
              <span>{{ uploadPercent }}%</span>
            </div>
            <el-progress
              :percentage="uploadPercent"
              :status="uploadElStatus"
              :stroke-width="10"
              striped
              striped-flow
            />
          </div>

          <div
            v-if="videoUrl"
            class="bg-green-50 p-4 rounded-md border border-green-200 flex items-start"
          >
            <el-icon class="text-green-500 mt-0.5 mr-2"><CircleCheckFilled /></el-icon>
            <div class="text-sm text-green-700 break-all">
              <p class="font-bold mb-1">发布成功！</p>
              播放地址：<a
                :href="videoUrl"
                target="_blank"
                class="underline hover:text-green-900"
                >{{ videoUrl }}</a
              >
            </div>
          </div>

          <div class="pt-4 flex justify-end">
            <el-button @click="$router.back()">取消</el-button>
            <el-button
              type="primary"
              @click="startUpload"
              :loading="uploading"
              :disabled="!selectedFile || !videoTitle"
            >
              {{ uploading ? '上传处理中...' : '开始上传' }}
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { VideoPlay, SuccessFilled, CircleCheckFilled } from '@element-plus/icons-vue'
import * as qiniu from 'qiniu-js'
import { MediaApi } from '@/api/media'

const router = useRouter()

// 状态
const videoTitle = ref('')
const selectedFile = ref<File | null>(null)
const fileInputRef = ref<HTMLInputElement>()

const uploading = ref(false)
const uploadPercent = ref(0)
const uploadStatus = ref<'ready' | 'uploading' | 'success' | 'error'>('ready')
const videoUrl = ref('')

// 计算属性
const uploadElStatus = computed(() => {
  if (uploadStatus.value === 'error') return 'exception'
  if (uploadStatus.value === 'success') return 'success'
  return ''
})

const uploadStatusText = computed(() => {
  if (uploadStatus.value === 'uploading') return '正在上传到云端...'
  if (uploadStatus.value === 'success') return '上传完成'
  if (uploadStatus.value === 'error') return '上传失败'
  return '准备就绪'
})

// 动作
const triggerFileSelect = () => {
  fileInputRef.value?.click()
}

const handleFileSelected = (e: Event) => {
  const files = (e.target as HTMLInputElement).files
  if (files && files[0]) {
    selectedFile.value = files[0]
    // 自动填充标题
    if (!videoTitle.value) {
      videoTitle.value = files[0].name.replace(/\.[^/.]+$/, '')
    }
    // 重置状态
    uploadStatus.value = 'ready'
    uploadPercent.value = 0
    videoUrl.value = ''
  }
}

const startUpload = async () => {
  if (!selectedFile.value || !videoTitle.value) return

  uploading.value = true
  uploadStatus.value = 'uploading'
  uploadPercent.value = 0

  try {
    // 1. 获取 Token
    const { token, domain } = await MediaApi.getUploadToken()

    // 2. 构造 Key (videos/时间戳_文件名)
    const key = `videos/${Date.now()}_${selectedFile.value.name}`

    // 3. 配置七牛
    const config = {
      useCdnDomain: true,
      region: qiniu.region.z1, // 华北区域
    }

    const putExtra = {
      // 自定义变量，可以在七牛回调中使用，这里暂时不用
    }

    // 4. 开始上传
    const observable = qiniu.upload(selectedFile.value, key, token, config, putExtra)

    observable.subscribe({
      next: (res) => {
        // 更新进度 (保留最后 5% 给后端保存数据用，提升体验)
        uploadPercent.value = Math.floor(res.total.percent * 0.95)
      },
      error: (err) => {
        console.error(err)
        ElMessage.error('云存储上传失败: ' + err.message)
        uploading.value = false
        uploadStatus.value = 'error'
      },
      complete: async (res) => {
        // 七牛传完了，开始调后端
        try {
          // 这里可以稍微假装跑一下进度条到 98%
          uploadPercent.value = 98

          await MediaApi.createVideo({
            title: videoTitle.value,
            file_key: res.key,
            file_hash: res.hash,
            file_size: res.fsize, // 七牛返回的 fsize
            duration: 0, // 目前七牛前端 SDK 不直接返回时长，需后端处理或前端解析
          })

          uploadPercent.value = 100
          uploadStatus.value = 'success'
          ElMessage.success('发布成功！')

          // 拼接播放地址
          const protocol = domain.startsWith('http') ? '' : 'http://'
          videoUrl.value = `${protocol}${domain}/${res.key}`
        } catch (dbError) {
          console.error(dbError)
          // 这里的错误已经被 request 拦截器处理了(弹窗)
          uploadStatus.value = 'error'
        } finally {
          uploading.value = false
        }
      },
    })
  } catch (error) {
    console.error(error)
    uploading.value = false
    uploadStatus.value = 'error'
  }
}
</script>
