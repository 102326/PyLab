// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import AIChat from '@/views/AIChat.vue'

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
      // 默认跳转到 AI，或者你可以做一个中间页
      redirect: '/chat/ai',
      children: [
        {
          path: 'user', // /chat/user
          name: 'user-chat',
          // ⚠️ 注意：这里引用的是改名后的 UserChatView.vue
          component: () => import('@/views/chat/UserChatView.vue'),
          meta: { title: '消息中心' },
        },
        {
          path: 'ai', // /chat/ai
          name: 'ai-chat',
          component: () => import('@/views/chat/AIChatView.vue'),
          meta: { title: 'AI 实验室' },
        },
        {
          path: '/teacher/course/:id/edit', // 编辑课程内容
          name: 'course-editor',
          component: () => import('../views/teacher/CourseEditor.vue'),
          meta: { requiresAuth: true, role: 1 }, // 仅讲师
        },
        {
          path: '/chat',
          name: 'AIChat',
          component: AIChat,
          meta: { title: 'AI 助教' },
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
