<script setup>
import { onMounted, computed, watch } from 'vue';
import { useWebSocket } from '@/stores/useWebSocket';
import { useUserStore } from '@/stores/user';

const userStore = useUserStore();
const { connect, close } = useWebSocket(); // 记得导出 close 方法

// 尝试初始化用户（从本地缓存）
userStore.initUser();

// 监听 userId 的变化
// 1. 如果用户从“未登录”变成“登录”，userId 有值 -> 自动连接
// 2. 如果用户“退出登录”，userId 变空 -> 自动断开
watch(
    () => userStore.userInfo?.id,
    (newId) => {
      if (newId) {
        console.log("检测到用户登录，建立 WS 连接:", newId);
        connect(newId);
      } else {
        console.log("用户退出，断开 WS 连接");
        close();
      }
    },
    { immediate: true } // 初始化时立即执行一次，覆盖 onMounted 的功能
);
</script>

<template>
  <router-view></router-view>
</template>