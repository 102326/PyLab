<template>
  <div class="dingtalk-wrapper flex justify-center">
    <div :id="containerId" class="bg-white"></div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  containerId: { type: String, default: 'dingtalk_login_box' },
})

const emit = defineEmits(['auth-code-received'])

// 配置 (建议放入 .env)
const clientId = 'ding1kq6asnilrnuhy36' // 你的 AppKey
// 这里的 redirectUri 必须和钉钉后台配置的一模一样 (http://localhost:5173/login)
const redirectUri = 'http://localhost:5173/login'

let isInit = false

const initDingTalkLogin = () => {
  if (isInit) return

  // TS 此时不知道 window 上有 DTFrameLogin，强转一下
  const w = window as any
  const DingTalkLogin = w.DTFrameLogin || w.DDLogin

  if (DingTalkLogin) {
    DingTalkLogin(
      {
        id: props.containerId,
        width: 365,
        height: 400,
      },
      {
        redirect_uri: redirectUri,
        client_id: clientId,
        scope: 'openid',
        response_type: 'code',
        state: 'STATE_' + Date.now(),
        prompt: 'consent',
      },
      (result: any) => {
        // 扫码成功，拿到 code
        if (result.authCode) {
          console.log('钉钉 Code:', result.authCode)
          emit('auth-code-received', result.authCode)
        }
      },
      (error: any) => {
        console.error('DingTalk SDK Error:', error)
        // 忽略超时错误
        if (error.code !== 'p_timeout') {
          // ElMessage.warning("扫码组件初始化异常")
        }
      },
    )
    isInit = true
  } else {
    // SDK 还没加载完，轮询
    setTimeout(initDingTalkLogin, 500)
  }
}

onMounted(() => {
  initDingTalkLogin()
})

onUnmounted(() => {
  isInit = false
})
</script>
