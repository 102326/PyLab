// src/composables/useWebSocket.js
import { ref } from 'vue'
import { ElNotification } from 'element-plus'
import { useUserStore } from '@/stores/user'

// 全局单例，保证整个 App 只有一个 socket 连接实例
let socket = null;
// 重连计时器
let reconnectTimer = null;

export function useWebSocket() {
    const isConnected = ref(false);

    // 初始化连接
    const connect = (userId) => {
        // 1. 如果已有连接且处于开启状态，不再重复连接
        if (socket && socket.readyState === WebSocket.OPEN) {
            console.log("WebSocket 已经是连接状态");
            isConnected.value = true;
            return;
        }

        // 2. 必须有 userId 才能连
        if (!userId) {
            console.warn("未提供 userId，无法建立 WebSocket 连接");
            return;
        }

        // 3. 动态拼接地址 (适配开发环境和生产环境 HTTPS)
        const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
        // 假设后端运行在 8000 端口，如果前后端同域则直接用 location.host
        const host = 'localhost:8000';
        const wsUrl = `${protocol}://${host}/ws/${userId}`;

        console.log(`正在连接 WebSocket: ${wsUrl}`);
        socket = new WebSocket(wsUrl);

        // --- 事件监听 ---
        socket.onopen = () => {
            console.log(`✅ WebSocket 连接成功 (User: ${userId})`);
            isConnected.value = true;
            // 连接成功后清除重连定时器
            if (reconnectTimer) clearTimeout(reconnectTimer);
        };

        socket.onmessage = (event) => {
            handleMessage(event.data);
        };

        socket.onclose = (e) => {
            console.log("❌ WebSocket 连接断开", e.code, e.reason);
            isConnected.value = false;
            socket = null;

            // 简单的断线重连机制 (5秒后重试)
            if (!reconnectTimer) {
                reconnectTimer = setTimeout(() => {
                    console.log("🔄 尝试重连 WebSocket...");
                    connect(userId);
                }, 5000);
            }
        };

        socket.onerror = (err) => {
            console.error("WebSocket 发生错误", err);
        };
    };

    // 统一消息处理函数
    const handleMessage = async (dataStr) => {
        try {
            const msg = JSON.parse(dataStr);
            const userStore = useUserStore(); // 获取 Store 实例

            if (msg.type === 'ocr_result') {
                if (msg.status === 'success') {
                    ElNotification({
                        title: '认证通过',
                        message: `恭喜！您的身份认证已自动完成。`,
                        type: 'success',
                        duration: 0,
                    });

                    // 【核心修复】: 收到通知后，通知 Store 刷新用户数据
                    // 这样 TeacherVerify 页面如果监听了 Store，就会自动变绿
                    await userStore.fetchTeacherProfile();

                    // 或者更简单粗暴：发布一个自定义事件，让页面监听
                    window.dispatchEvent(new CustomEvent('ocr-completed', { detail: msg.data }));

                } else {
                    ElNotification({
                        title: '认证驳回',
                        message: msg.msg || '识别失败，请检查图片清晰度',
                        type: 'error',
                        duration: 5000
                    });
                }
            }

            // 场景 2: 其他通知 (例如系统公告)
            else if (msg.type === 'system_notice') {
                ElNotification.info({ title: '系统通知', message: msg.content });
            }

        } catch (e) {
            // 容错：有些心跳包可能是纯文本 "pong"
            if (dataStr === 'pong') return;
            console.error("消息解析失败:", e);
        }
    };

    // 手动断开
    const close = () => {
        if (socket) {
            socket.close();
            socket = null;
        }
    };

    return {
        connect,
        close,
        isConnected
    };
}