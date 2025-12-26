import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
const LoginView = () => import('@/views/LoginView.vue')
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login', // 暂时先把首页重定向到登录
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/user',
      name: 'user',
      component: () => import('@/views/UserCenter.vue'),
    },
    // 临时把首页重定向到 user，方便调试
    {
      path: '/home',
      redirect: '/user',
    },
    {
      path: '/teacher/verify',
      name: 'TeacherVerify',
      component: () => import('@/views/teacher/Verify.vue'),
    },
    // [新增] 上传页
    {
      path: '/upload',
      name: 'Upload',
      component: () => import('@/views/teacher/Upload.vue'),
    },
  ],
})

export default router
