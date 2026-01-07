// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
      meta: { title: '首页' },
    },
    {
      path: '/course/:id',
      name: 'course-detail',
      component: () => import('@/views/course/Detail.vue'),
      meta: { title: '课程详情', isPublic: true },
    },
    // [新增] 课程播放页 (需要登录)
    {
      path: '/course/:id/learn',
      name: 'course-player',
      component: () => import('@/views/course/Player.vue'),
      meta: { requiresAuth: true, title: '课程学习' },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { title: '登录', isPublic: true },
    },
    {
      path: '/teacher/verify',
      name: 'teacher-verify',
      component: () => import('@/views/teacher/Verify.vue'),
      meta: { requiresAuth: true, title: '讲师认证' },
    },
    {
      path: '/teacher/upload',
      name: 'teacher-upload',
      component: () => import('@/views/teacher/Upload.vue'),
      meta: { requiresAuth: true, title: '发布课程' },
    },
    {
      path: '/user',
      name: 'user-center',
      component: () => import('@/views/UserCenter.vue'),
      meta: { requiresAuth: true, title: '个人中心' },
    },
    // === [核心修改] 聊天路由拆分 ===
    {
      path: '/chat',
      meta: { title: '消息中心', requiresAuth: true },
      // 1. 默认重定向到 AI 页面，避免空屏
      redirect: '/chat/ai',
      children: [
        // === 1. 私信模块 (保留原样) ===
        {
          path: 'user', // 访问路径: /chat/user
          name: 'user-chat',
          component: () => import('@/views/chat/UserChatView.vue'),
          meta: { title: '消息中心' },
        },

        // === 2. AI 模块 (使用新版流式页面) ===
        {
          path: 'ai', // 访问路径: /chat/ai
          name: 'ai-chat',
          // ⚠️ 重点：指向新写的、支持流式输出的 AIChatView.vue
          component: () => import('@/views/chat/AIChatView.vue'),
          meta: { title: 'AI 实验室' },
        },
        {
          path: '/teacher/course/:id/edit',
          name: 'course-editor',
          component: () => import('@/views/teacher/CourseEditor.vue'),
          meta: { requiresAuth: true, role: 1 }, // 仅讲师
        },
      ],
    },
  ],
})

// 白名单
const whiteList = ['/login', '/register', '/']

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  document.title = `${to.meta.title || 'PyLab'} - 在线教育平台`

  const hasToken = !!userStore.token

  if (hasToken) {
    if (to.path === '/login') {
      next({ path: '/' })
    } else {
      next()
    }
  } else {
    if (whiteList.includes(to.path) || to.meta.isPublic) {
      next()
    } else {
      next(`/login?redirect=${to.fullPath}`)
    }
  }
})

export default router
