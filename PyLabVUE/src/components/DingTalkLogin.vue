<template>
  <div class="dingtalk-wrapper">
    <div :id="containerId" class="login-container"></div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue';
import { ElMessage } from 'element-plus';

const props = defineProps({
  // 允许父组件传入 ID，避免潜在的 DOM ID 冲突
  containerId: { type: String, default: "dingtalk_login_box" }
});

const emit = defineEmits(['auth-code-received']);

// === 配置区 (建议后续提取到环境变量) ===
const clientId = "ding1kq6asnilrnuhy36"; // 你的 AppKey
const redirectUri = "http://localhost:5173/login"; // 必须与钉钉后台一致

let isInit = false;

const initDingTalkLogin = () => {
  if (isInit) return;

  // 使用你验证成功的 DTFrameLogin
  const DingTalkLogin = window.DTFrameLogin || window.DDLogin;

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
          scope: "openid",
          response_type: "code",
          state: "STATE_" + Date.now(), // 随机 State 防缓存
          prompt: "consent",
        },
        (result) => {
          // === 核心变化：只 emit，不发请求 ===
          if (result.authCode) {
            console.log("扫码成功，Code:", result.authCode);
            emit('auth-code-received', result.authCode);
          }
        },
        (error) => {
          console.error("DingTalk SDK Error:", error);
          // 某些超时错误可以忽略，不弹窗
          if (error.code !== 'p_timeout') {
            ElMessage.warning("扫码组件初始化异常");
          }
        }
    );
    isInit = true;
  } else {
    // SDK 未加载完成，轮询重试
    setTimeout(initDingTalkLogin, 500);
  }
};

onMounted(() => {
  initDingTalkLogin();
});

// 这是一个良好的习惯：组件销毁时标记状态，虽然后端SDK通常不需要显式销毁
onUnmounted(() => {
  isInit = false;
});
</script>

<style scoped>
.login-container {
  width: 365px;
  height: 400px;
  background: #fff;
  margin: 0 auto;
}
</style>