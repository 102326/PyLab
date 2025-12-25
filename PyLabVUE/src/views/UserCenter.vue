<template>
  <div class="user-center-container">
    <el-container class="layout-container">

      <el-aside width="200px" class="aside-menu">
        <div class="logo-area">PyLab Center</div>
        <el-menu default-active="1" class="menu-vertical">
          <el-menu-item index="1">
            <span>个人资料</span>
          </el-menu-item>
          <el-menu-item index="2">
            <span>账号安全</span>
          </el-menu-item>
          <el-menu-item index="3" disabled>
            <span>会员订阅 (Pro)</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-main class="main-body">
        <div class="profile-card">
          <div class="card-header">
            <h3>基本信息</h3>
            <div class="header-actions">
              <el-button type="warning" plain @click="router.push('/teacher/verify')">
                教师实名认证
              </el-button>
              <el-button type="primary" link>编辑资料</el-button>
            </div>
          </div>

          <div class="info-layout">
            <div class="avatar-section">
              <el-avatar :size="100" :src="userInfo.avatar || defaultAvatar" />
              <div class="role-badge">普通用户</div>
            </div>

            <div class="details-section">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="昵称">{{ userInfo.nickname || '未设置昵称' }}</el-descriptions-item>
                <el-descriptions-item label="用户ID">#{{ userInfo.id || '0000' }}</el-descriptions-item>
                <el-descriptions-item label="用户名">{{ userInfo.username || 'user_unknown' }}</el-descriptions-item>
                <el-descriptions-item label="注册时间">{{ userInfo.createTime || '2025-01-01 (Mock)' }}</el-descriptions-item>
                <el-descriptions-item label="个性签名">
                  {{ userInfo.bio || '这个人很懒，什么都没有写...' }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </div>

          <div class="action-footer">
            <el-button type="danger" plain @click="handleLogout">退出登录</el-button>
          </div>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import axios from 'axios';

const router = useRouter();
const defaultAvatar = "https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png";

// 响应式用户数据
const userInfo = ref({
  id: '',
  username: '',
  nickname: '',
  avatar: '',
  // 以下是死数据，后端暂时没返回
  bio: '正在学习 FastAPI + Vue3 全栈开发',
  createTime: '2025-12-23'
});

onMounted(() => {
  // 1. 尝试从 LocalStorage 获取登录时存的信息
  const cachedUser = localStorage.getItem('user_info');
  const token = localStorage.getItem('token');

  if (!token) {
    ElMessage.warning('请先登录');
    router.push('/login');
    return;
  }

  if (cachedUser) {
    //如果有缓存，先显示缓存
    try {
      const parsed = JSON.parse(cachedUser);
      userInfo.value = { ...userInfo.value, ...parsed };
    } catch(e) {}
  }

  // 2. (可选) 这里应该调用后端 /api/auth/me 接口获取最新数据
  // fetchLatestUserInfo();
});

const handleLogout = () => {
  // 清理本地存储
  localStorage.removeItem('token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_info');

  ElMessage.success('已退出登录');
  router.push('/login');
};
</script>

<style scoped>
.user-center-container {
  height: 100vh;
  background-color: #f5f7fa;
}
.layout-container {
  height: 100%;
  max-width: 1200px;
  margin: 0 auto;
}
.aside-menu {
  background-color: white;
  margin-right: 20px;
  height: 100%;
}
.logo-area {
  height: 60px;
  line-height: 60px;
  text-align: center;
  font-weight: bold;
  font-size: 18px;
  color: #409EFF;
  border-bottom: 1px solid #eee;
}
.main-body {
  padding: 20px 0;
}
.profile-card {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.05);
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #eee;
  padding-bottom: 15px;
  margin-bottom: 20px;
}
.info-layout {
  display: flex;
  gap: 40px;
}
.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 150px;
}
.role-badge {
  margin-top: 10px;
  background: #ecf5ff;
  color: #409eff;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
}
.details-section {
  flex: 1;
}
.action-footer {
  margin-top: 40px;
  text-align: right;
  border-top: 1px solid #eee;
  padding-top: 20px;
}
</style>