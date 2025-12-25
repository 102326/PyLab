// src/stores/user.js
import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request';

export const useUserStore = defineStore('user', () => {
    // 状态：用户信息
    const userInfo = ref(null)
    const token = ref(localStorage.getItem('token') || '')

    // 动作：登录成功后保存信息
    function setUser(data) {
        userInfo.value = data
        // 假设 data 结构是 { id: 1, username: 'admin', ... }
        // 也可以顺便持久化到 localStorage 防止刷新丢失
        localStorage.setItem('user_info', JSON.stringify(data))
    }

    // 动作：初始化（刷新页面时从 localStorage 恢复）
    function initUser() {
        const stored = localStorage.getItem('user_info')
        if (stored) {
            try {
                userInfo.value = JSON.parse(stored)
            } catch (e) {
                console.error("解析用户信息失败", e)
            }
        }
    }

    async function fetchTeacherProfile() {
        try {
            // 假设你有一个接口获取当前用户的档案
            // 如果没有，建议在后端 /api/auth/me 里带上 teacher_profile 信息
            const res = await request.get('/api/auth/me');
            // 更新 Store 或返回数据给组件使用
            return res.data.data.teacher_profile;
        } catch (e) {
            console.error(e);
        }
    }
    return { userInfo, token, setUser, initUser, fetchTeacherProfile}
})