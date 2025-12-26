import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { UserInfo } from '@/model/auth'
import { AuthApi } from '@/api/auth'
export const useUserStore = defineStore('user', () => {
  // 1. State (状态)
  const token = ref<string>(localStorage.getItem('token') || '')
  const userInfo = ref<UserInfo | null>(null)

  // 2. Actions (动作)

  // 设置登录状态
  function setLoginState(newToken: string, user: UserInfo) {
    token.value = newToken
    userInfo.value = user
    // 持久化存储
    localStorage.setItem('token', newToken)
    localStorage.setItem('user_info', JSON.stringify(user))
  }

  // 登出
  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user_info')
  }

  // 初始化（刷新页面时恢复数据）
  function initUser() {
    const storedUser = localStorage.getItem('user_info')
    if (storedUser) {
      try {
        userInfo.value = JSON.parse(storedUser)
      } catch (e) {
        console.error('解析用户信息失败', e)
      }
    }
  }

  async function refreshUserInfo() {
    try {
      // 调用 getMe 接口 (假设它返回完整的 MeRes)
      const data = await AuthApi.getMe()
      // 更新 store 中的基本信息
      userInfo.value = data.user_info
      localStorage.setItem('user_info', JSON.stringify(data.user_info))
      // 返回完整数据供调用者使用 (比如 socket store 需要 teacher_profile)
      return data
    } catch (error) {
      console.error('刷新用户信息失败', error)
    }
  }

  return { token, userInfo, setLoginState, logout, initUser, refreshUserInfo }
})
