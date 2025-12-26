<template>
  <div class="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-xl mx-auto">
      <div class="text-center mb-10">
        <h2 class="text-3xl font-extrabold text-gray-900">讲师实名认证</h2>
        <p class="mt-2 text-sm text-gray-600">我们需要验证您的身份信息以保障平台内容质量</p>
      </div>

      <div class="bg-white py-8 px-6 shadow rounded-lg sm:px-10">
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 mb-2">身份证人像面</label>
          <div
            class="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md cursor-pointer hover:border-indigo-500 transition-colors relative"
            @click="triggerUpload('front')"
          >
            <img v-if="frontUrl" :src="frontUrl" class="h-48 object-contain" />

            <div v-else class="space-y-1 text-center">
              <el-icon class="mx-auto h-12 w-12 text-gray-400 text-4xl"><UploadFilled /></el-icon>
              <div class="flex text-sm text-gray-600 justify-center">
                <span
                  class="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500"
                >
                  点击上传
                </span>
              </div>
              <p class="text-xs text-gray-500">支持 JPG, PNG, Max 5MB</p>
            </div>

            <input
              type="file"
              ref="frontInput"
              class="hidden"
              accept="image/*"
              @change="(e) => handleFileChange(e, 'front')"
            />

            <div
              v-if="uploadStatus.front.loading"
              class="absolute inset-0 bg-white/80 flex items-center justify-center"
            >
              <el-progress type="circle" :percentage="uploadStatus.front.percent" />
            </div>
          </div>
        </div>

        <div class="mb-8">
          <label class="block text-sm font-medium text-gray-700 mb-2">身份证国徽面</label>
          <div
            class="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md cursor-pointer hover:border-indigo-500 transition-colors relative"
            @click="triggerUpload('back')"
          >
            <img v-if="backUrl" :src="backUrl" class="h-48 object-contain" />

            <div v-else class="space-y-1 text-center">
              <el-icon class="mx-auto h-12 w-12 text-gray-400 text-4xl"><UploadFilled /></el-icon>
              <div class="flex text-sm text-gray-600 justify-center">
                <span
                  class="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500"
                >
                  点击上传
                </span>
              </div>
            </div>

            <input
              type="file"
              ref="backInput"
              class="hidden"
              accept="image/*"
              @change="(e) => handleFileChange(e, 'back')"
            />
            <div
              v-if="uploadStatus.back.loading"
              class="absolute inset-0 bg-white/80 flex items-center justify-center"
            >
              <el-progress type="circle" :percentage="uploadStatus.back.percent" />
            </div>
          </div>
        </div>

        <button
          @click="handleSubmit"
          :disabled="!isReady || submitting"
          class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {{ submitting ? '提交审核中...' : '提交认证' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import * as qiniu from 'qiniu-js' // 引入七牛 SDK
import { MediaApi } from '@/api/media'

const router = useRouter()
const frontInput = ref<HTMLInputElement>()
const backInput = ref<HTMLInputElement>()

// 图片地址 (存的是完整的 URL)
const frontUrl = ref('')
const backUrl = ref('')

// 上传状态管理
const uploadStatus = reactive({
  front: { loading: false, percent: 0 },
  back: { loading: false, percent: 0 },
})

const submitting = ref(false)
const isReady = computed(() => frontUrl.value && backUrl.value)

// 触发文件选择
const triggerUpload = (type: 'front' | 'back') => {
  if (type === 'front') frontInput.value?.click()
  else backInput.value?.click()
}

// 处理文件选择 & 上传七牛云
const handleFileChange = async (e: Event, type: 'front' | 'back') => {
  const files = (e.target as HTMLInputElement).files
  if (!files || files.length === 0) return

  const file = files[0]
  const status = uploadStatus[type]

  try {
    status.loading = true

    // 1. 获取 Token
    const { token, domain } = await MediaApi.getUploadToken()

    // 2. 构造文件名 (避免重名覆盖: idcard/随机串_文件名)
    const key = `idcard/${Date.now()}_${Math.random().toString(36).slice(2)}`

    // 3. 调用七牛 SDK 上传
    const observable = qiniu.upload(file, key, token, {}, { useCdnDomain: true })

    observable.subscribe({
      next(res) {
        // 更新进度条
        status.percent = Math.floor(res.total.percent)
      },
      error(err) {
        console.error(err)
        ElMessage.error('图片上传失败')
        status.loading = false
      },
      complete(res) {
        // 上传成功，拼接完整 URL
        // 注意：七牛返回的 res.key 就是我们传进去的 key
        // 假设 domain 不带 http，需要拼接；如果带了就直接拼
        const protocol = domain.startsWith('http') ? '' : 'http://'
        const fullUrl = `${protocol}${domain}/${res.key}`

        if (type === 'front') frontUrl.value = fullUrl
        else backUrl.value = fullUrl

        status.loading = false
        ElMessage.success('上传成功')
      },
    })
  } catch (error) {
    console.error(error)
    ElMessage.error('获取上传凭证失败')
    status.loading = false
  }
}

// 提交给后端
const handleSubmit = async () => {
  if (!isReady.value) return

  submitting.value = true
  try {
    await MediaApi.verifyIdCard({
      front_url: frontUrl.value,
      back_url: backUrl.value,
    })

    ElMessage.success('提交成功！请耐心等待审核')
    // 返回个人中心
    router.push('/user')
  } catch (error) {
    console.error(error)
  } finally {
    submitting.value = false
  }
}
</script>
