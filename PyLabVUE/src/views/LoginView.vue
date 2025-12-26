<template>
  <div
    class="h-screen w-full flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100"
  >
    <div class="bg-white w-full max-w-md p-8 rounded-2xl shadow-xl transition-all hover:shadow-2xl">
      <div class="text-center mb-6">
        <h1 class="text-3xl font-bold text-gray-800 mb-2">PyLab</h1>
        <p class="text-gray-500 text-sm">
          {{ isRegister ? '创建新账号' : '开启你的代码学习之旅' }}
        </p>
      </div>

      <div
        v-if="!isRegister"
        class="flex justify-center mb-6 space-x-6 border-b border-gray-100 pb-2"
      >
        <span
          class="cursor-pointer pb-2 border-b-2 transition-all duration-300 px-2"
          :class="
            loginMethod === 'password'
              ? 'border-blue-500 text-blue-600 font-bold'
              : 'border-transparent text-gray-400 hover:text-gray-600'
          "
          @click="loginMethod = 'password'"
        >
          账号密码
        </span>
        <span
          class="cursor-pointer pb-2 border-b-2 transition-all duration-300 px-2"
          :class="
            loginMethod === 'dingtalk'
              ? 'border-blue-500 text-blue-600 font-bold'
              : 'border-transparent text-gray-400 hover:text-gray-600'
          "
          @click="loginMethod = 'dingtalk'"
        >
          钉钉扫码
        </span>
      </div>

      <div v-if="isRegister || loginMethod === 'password'" class="animate-fade-in">
        <el-form ref="formRef" :model="form" :rules="rules" size="large" class="space-y-4">
          <el-form-item prop="phone">
            <el-input v-model="form.phone" placeholder="手机号" :prefix-icon="UserIcon" />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="密码"
              show-password
              :prefix-icon="Lock"
              @keyup.enter="handleSubmit"
            />
          </el-form-item>

          <div v-if="isRegister" class="animate-fade-in-down">
            <el-form-item prop="role">
              <el-radio-group v-model="form.role" class="w-full !flex">
                <el-radio-button :value="0" class="flex-1 text-center">我是学生</el-radio-button>
                <el-radio-button :value="1" class="flex-1 text-center">我是老师</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <p class="text-xs text-gray-400 mt-1 text-center">
              * 老师账号需完成实名认证后方可发布课程
            </p>
          </div>

          <el-button
            type="primary"
            :loading="loading"
            class="!w-full !rounded-full !h-12 !text-lg !font-semibold mt-4 bg-gradient-to-r from-blue-500 to-indigo-600 border-none hover:opacity-90"
            @click="handleSubmit"
          >
            {{ isRegister ? '立即注册' : '登录' }}
          </el-button>

          <div class="flex justify-between text-sm text-gray-500 mt-4">
            <span class="cursor-pointer hover:text-blue-600" v-if="!isRegister">忘记密码?</span>
            <span class="flex-1"></span>
            <span class="cursor-pointer text-blue-600 font-semibold" @click="toggleMode">
              {{ isRegister ? '已有账号？去登录' : '没有账号？注册新账号' }}
            </span>
          </div>
        </el-form>
      </div>

      <div v-else class="flex justify-center py-4 animate-fade-in">
        <DingTalkLogin @auth-code-received="handleDingTalkCode" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User as UserIcon, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { AuthApi } from '@/api/auth'
import type { LoginReq } from '@/model/auth'
import DingTalkLogin from '@/components/DingTalkLogin.vue' // 引入组件

const router = useRouter()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const isRegister = ref(false) // 是否处于注册模式
const loginMethod = ref<'password' | 'dingtalk'>('password') // 登录方式

// 表单数据
const form = reactive<LoginReq>({
  login_type: 'password',
  phone: '',
  password: '',
  role: 0,
})

// 校验规则
const rules = computed<FormRules>(() => ({
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  ...(isRegister.value
    ? {
        role: [{ required: true, message: '请选择角色', trigger: 'change' }],
      }
    : {}),
}))

// 切换 注册/登录
const toggleMode = () => {
  isRegister.value = !isRegister.value
  loginMethod.value = 'password' // 重置回密码登录
  if (formRef.value) formRef.value.clearValidate()
}

// 账号密码提交
const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        if (isRegister.value) {
          // === 注册 ===
          await AuthApi.register(form)
          ElMessage.success('注册成功，请登录')
          isRegister.value = false
        } else {
          // === 密码登录 ===
          const data = await AuthApi.login({ ...form, login_type: 'password' })
          handleLoginSuccess(data)
        }
      } catch (error) {
        console.error(error)
      } finally {
        loading.value = false
      }
    }
  })
}

// 钉钉扫码回调
const handleDingTalkCode = async (code: string) => {
  // 注意：钉钉登录时 loading 可能不太好显示在按钮上，可以用全屏 loading 或 toast
  const loadingInstance = ElMessage.info({ message: '正在登录中...', duration: 0 })
  try {
    const data = await AuthApi.login({
      login_type: 'dingtalk',
      auth_code: code,
    })
    loadingInstance.close()
    handleLoginSuccess(data)
  } catch (error) {
    loadingInstance.close()
    console.error(error)
  }
}

// 统一登录成功处理
const handleLoginSuccess = (data: any) => {
  userStore.setLoginState(data.access_token, data.user_info)
  ElMessage.success(`欢迎回来，${data.user_info.nickname}`)
  router.push('/user')
}
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}
.animate-fade-in-down {
  animation: fadeInDown 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

:deep(.el-radio-group) {
  display: flex;
}
:deep(.el-radio-button__inner) {
  width: 100%;
  padding: 10px 0;
}
</style>
