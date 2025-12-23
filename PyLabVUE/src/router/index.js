import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import UserCenter from "@/views/UserCenter.vue";
import TeacherUpload from "@/views/TeacherUpload.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/user',
      name: 'UserCenter',
      component: UserCenter,
      // 可以在这里加路由守卫，未登录不准进
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/LoginView.vue'),
    },
    {
      path: '/upload',
      name: 'Upload',
      component: TeacherUpload
    }
  ],
})

export default router
