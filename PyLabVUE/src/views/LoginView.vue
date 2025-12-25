<template>
  <div class="login-bg">
    <div class="login-card">

      <div class="header">
        <h2 class="app-title">PyLab</h2>
        <p class="sub-title">开启你的 代码学习 之旅</p>
      </div>

      <div class="main-content">

        <div v-show="loginMethod === 'password'" class="form-container">
          <el-form
              ref="loginFormRef"
              :model="form"
              :rules="rules"
              size="large"
              @keyup.enter="handlePasswordLogin"
          >
            <el-form-item prop="phone">
              <el-input v-model="form.phone" placeholder="邮箱 / 用户名" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="form.password" type="password" placeholder="密码" show-password />
            </el-form-item>

            <el-button type="primary" class="action-btn login-btn" :loading="loading" @click="handlePasswordLogin">
              登录
            </el-button>
            <el-button class="action-btn register-btn" @click="handleRegister">
              注册账号
            </el-button>
          </el-form>
        </div>

        <div v-show="loginMethod === 'dingtalk'" class="qr-container">
          <div class="qr-header">
            <span>请使用钉钉扫码</span>
            <el-button link type="primary" @click="loginMethod = 'password'">返回账号登录</el-button>
          </div>
          <DingTalkLogin v-if="loginMethod === 'dingtalk'" @auth-code-received="handleDingTalkLogin" />
        </div>

      </div>

      <div class="footer-divider">
        <span>用其他账号登录</span>
      </div>

      <div class="social-login-group">
        <el-tooltip content="钉钉登录" placement="bottom">
          <div class="social-btn dingtalk-btn" @click="loginMethod = 'dingtalk'">
            <span>钉</span>
          </div>
        </el-tooltip>

        <el-tooltip content="QQ登录 (暂未开放)" placement="bottom">
          <div class="social-btn qq-btn disabled">Q</div>
        </el-tooltip>

        <el-tooltip content="微信登录 (暂未开放)" placement="bottom">
          <div class="social-btn wechat-btn disabled">微</div>
        </el-tooltip>
      </div>

      <div class="terms">
        登录即代表您同意 <a href="#">服务条款</a> 和 <a href="#">隐私政策</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import axios from 'axios';
import { useRouter } from 'vue-router';
import DingTalkLogin from '../components/DingTalkLogin.vue';

const router = useRouter();
const loginMethod = ref('password'); // 当前显示的模式：'password' | 'dingtalk'
const loading = ref(false);
const loginFormRef = ref(null);

const form = reactive({ phone: '', password: '' });
const rules = {
  phone: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
};

// ... (handlePasswordLogin, handleDingTalkLogin, handleRegister 逻辑与之前保持一致，此处省略以节省篇幅) ...
// 记得把之前的 performLogin 等函数复制过来
// === 核心逻辑复用开始 ===
const performLogin = async (payload) => {
  loading.value = true;
  try {
    const res = await axios.post('/api/auth/login', payload);
    const { data, msg } = res.data;
    localStorage.setItem('token', data.access_token);
    // 简单存一下用户信息，方便个人中心取用
    localStorage.setItem('user_info', JSON.stringify(data.user_info));

    ElMessage.success(msg || `欢迎回来`);
    router.push('/user'); // 登录成功跳转到【个人中心】
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '登录请求失败');
  } finally {
    loading.value = false;
  }
};

const handlePasswordLogin = async () => {
  if (!loginFormRef.value) return;
  await loginFormRef.value.validate((valid) => {
    if (valid) performLogin({ login_type: 'password', ...form });
  });
};

const handleDingTalkLogin = (authCode) => {
  performLogin({ login_type: 'dingtalk', auth_code: authCode });
};

const handleRegister = () => {
  // 简易注册演示
  ElMessageBox.prompt('请输入密码', '注册新用户 (用户名)', { inputPlaceholder: '用户名' })
      .then(async ({ value: phone }) => {
        const password = prompt("请设置密码:");
        if(phone && password) {
          try {
            await axios.post('/api/auth/register', { login_type: 'password', phone, password });
            ElMessage.success("注册成功");
          } catch(e) { ElMessage.error("注册失败"); }
        }
      });
};
// === 核心逻辑复用结束 ===
</script>

<style scoped>
.login-bg {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f2f4f6; /* Pixiv 风格浅灰底色 */
  /* background-image: url('你的背景图.jpg'); */
  background-size: cover;
}

.login-card {
  width: 400px;
  background: #ffffff;
  border-radius: 4px; /* Pixiv 卡片圆角较小 */
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  padding: 40px 32px;
  text-align: center;
}

.app-title {
  color: #0096fa; /* Pixiv 蓝 */
  font-weight: bold;
  font-size: 28px;
  margin-bottom: 8px;
}
.sub-title {
  color: #5c5c5c;
  font-size: 14px;
  margin-bottom: 30px;
}

.action-btn {
  width: 100%;
  height: 40px;
  font-weight: bold;
  border-radius: 20px; /* 圆角按钮 */
  margin-left: 0 !important; /* 覆盖 el-button 默认间距 */
}

.login-btn {
  background-color: #0096fa;
  border-color: #0096fa;
  margin-bottom: 12px;
}

.register-btn {
  background-color: #f5f5f5;
  border-color: #f5f5f5;
  color: #333;
}
.register-btn:hover {
  background-color: #e0e0e0;
}

/* 分割线 */
.footer-divider {
  margin: 30px 0 20px;
  position: relative;
  text-align: center;
}
.footer-divider::before {
  content: "";
  position: absolute;
  top: 50%;
  left: 0;
  width: 100%;
  height: 1px;
  background: #ebebeb;
  z-index: 0;
}
.footer-divider span {
  position: relative;
  background: #fff;
  padding: 0 10px;
  color: #adadad;
  font-size: 12px;
  z-index: 1;
}

/* 社交图标组 */
.social-login-group {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 20px;
}

.social-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.2s;
  font-weight: bold;
  color: white;
  font-size: 14px;
}
.social-btn:hover {
  transform: scale(1.1);
}

.dingtalk-btn {
  background-color: #0089FF; /* 钉钉蓝 */
  box-shadow: 0 2px 8px rgba(0, 137, 255, 0.3);
}

.qq-btn, .wechat-btn {
  background-color: #eee;
  color: #999;
  cursor: not-allowed;
}

/* 二维码区域样式 */
.qr-container {
  min-height: 300px;
}
.qr-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 14px;
  color: #666;
}

.terms {
  font-size: 12px;
  color: #999;
  margin-top: 20px;
}
.terms a {
  color: #333;
  text-decoration: none;
}
</style>