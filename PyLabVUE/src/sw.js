// src/sw.js

// self 指向 Service Worker 全局作用域
self.addEventListener('install', (event) => {
  console.log('[Service Worker] 安装成功')
  // 强制立即激活新的 Service Worker
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  console.log('[Service Worker] 激活成功')
  // 让 Service Worker 立即接管所有页面
  event.waitUntil(self.clients.claim())
})

// Let's define a placeholder for the push event now
// 核心：监听来自浏览器厂商服务器的推送事件
self.addEventListener('push', function (event) {
  console.log('[Service Worker] 收到推送消息', event)

  let data = { title: '新消息', body: '您有一条新消息' }

  if (event.data) {
    try {
      // 解析后端发送过来的 JSON 数据
      data = event.data.json()
      console.log('推送数据:', data)
    } catch (e) {
      console.warn('推送数据不是 JSON 格式，使用纯文本')
      data.body = event.data.text()
    }
  }

  const title = data.title || '新消息'
  const options = {
    body: data.body,
    icon: '/favicon.ico', // 确保这个路径下有图标
    badge: '/favicon.ico', // 安卓状态栏小图标
    data: data.url || '/', // 点击通知后跳转的链接存这里
    vibrate: [100, 50, 100],
    actions: [
      { action: 'explore', title: '查看' },
      { action: 'close', title: '关闭' },
    ],
  }

  // 弹出系统通知
  event.waitUntil(self.registration.showNotification(title, options))
})

// 监听通知点击事件
self.addEventListener('notificationclick', function (event) {
  console.log('[Service Worker] 通知被点击')
  event.notification.close() // 关闭通知

  if (event.action === 'close') return

  // 点击通知后，尝试打开或聚焦到应用的窗口
  event.waitUntil(
    self.clients
      .matchAll({ type: 'window', includeUncontrolled: true })
      .then(function (clientList) {
        // 如果已经有窗口打开了，就聚焦它
        for (let i = 0; i < clientList.length; i++) {
          const client = clientList[i]
          if (client.url.includes(self.registration.scope) && 'focus' in client) {
            return client.focus()
          }
        }
        // 如果没有窗口打开，就新开一个
        if (clients.openWindow) {
          // 这里可以取上面存的 data.url 跳到特定页面
          return clients.openWindow('/')
        }
      }),
  )
})
