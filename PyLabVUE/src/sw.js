// src/sw.js

self.addEventListener('install', (event) => {
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim())
})

// === 核心：接收推送 ===
self.addEventListener('push', function (event) {
  console.log('[Service Worker] 收到推送消息', event)

  let data = {
    title: '新私信',
    body: '您收到一条新消息',
    url: '/chat/user' // ⚡️ 默认跳转到私信页面
  }

  if (event.data) {
    try {
      const jsonPayload = event.data.json()
      // 合并后端发来的数据
      data = { ...data, ...jsonPayload }
      // 确保后端发来的 url 字段被使用，如果没有，回退到 /chat/user
      if (!data.url) data.url = '/chat/user'
    } catch (e) {
      data.body = event.data.text()
    }
  }

  const options = {
    body: data.body,
    icon: '/favicon.ico',
    badge: '/favicon.ico',
    // ⚡️ 将跳转链接存在 data 属性里，供点击事件使用
    data: { url: data.url },
    vibrate: [100, 50, 100],
    actions: [
      { action: 'explore', title: '回复' },
      { action: 'close', title: '关闭' },
    ],
  }

  event.waitUntil(self.registration.showNotification(data.title, options))
})

// === 核心：点击通知 ===
self.addEventListener('notificationclick', function (event) {
  event.notification.close() // 关闭通知面板

  if (event.action === 'close') return

  // 获取之前存在 options.data 里的链接
  const urlToOpen = event.notification.data.url || '/chat/user'

  event.waitUntil(
    self.clients
      .matchAll({ type: 'window', includeUncontrolled: true })
      .then(function (clientList) {
        // 1. 尝试寻找已经打开的本应用窗口
        for (let i = 0; i < clientList.length; i++) {
          const client = clientList[i]
          // 只要是本域名的窗口
          if (client.url.includes(self.registration.scope) && 'focus' in client) {
            // 聚焦窗口并跳转到指定页面
            return client.focus().then(c => c.navigate(urlToOpen))
          }
        }
        // 2. 如果没有打开，则新开窗口
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen)
        }
      }),
  )
})
