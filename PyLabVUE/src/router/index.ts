// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user' // 引入 User Store

// 1. 定义路由表
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      // 如果你想让首页作为“课程大厅”公开访问，就不要加 meta: { requiresAuth: true }
      // 如果首页必须登录才能看，那就保留 meta
      component: () => import('@/views/HomeView.vue'),
      meta: { title: '首页' },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { title: '登录', isPublic: true }, // 标记为公开页面
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
    // 404 页面 (可选)
    // { path: '/:pathMatch(.*)*', redirect: '/' }
  ],
})

// 2. 路由白名单 (不需要登录就能访问的页面)
const whiteList = ['/login', '/register', '/']

// 3. 全局前置守卫
router.beforeEach((to, from, next) => {
  // 必须在 guard 内部获取 store，否则会报错 "Pinia not installed"
  const userStore = useUserStore()

  // 设置页面标题
  document.title = `${to.meta.title || 'PyLab'} - 在线教育平台`

  // A. 判断是否有 Token
  const hasToken = !!userStore.token

  if (hasToken) {
    // === 已登录 ===
    if (to.path === '/login') {
      // 如果已登录还要去登录页，强制踢回首页
      next({ path: '/' })
    } else {
      // 去其他页面，放行
      next()
    }
  } else {
    // === 未登录 ===
    // 判断要去的地方是不是白名单 (或者有 meta.isPublic)
    if (whiteList.includes(to.path) || to.meta.isPublic) {
      next() // 是白名单，放行
    } else {
      // 不是白名单，也就是受保护页面 -> 踢回登录页
      // redirect 参数用于登录后自动跳回刚才想去的页面
      next(`/login?redirect=${to.fullPath}`)
    }
  }
})

export default router
