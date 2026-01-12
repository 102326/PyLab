# D:\daima\PyLab\PyLabFastAPI\app\core\socket_manager.py

import asyncio
import json
import logging
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect
import aio_pika
from app.core.mq import RabbitMQClient

logger = logging.getLogger("uvicorn")


class ConnectionManager:
    def __init__(self):
        # 存放 WebSocket 连接 {user_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # 存放 MQ 信道 {user_id: channel}
        self.mq_channels: Dict[str, aio_pika.Channel] = {}
        # 存放后台监听任务 {user_id: task}
        self.listening_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        """处理新连接"""
        await websocket.accept()

        # 1. 强制清理旧连接 (防止同一个用户多端登录导致消息错乱，或者处理僵尸连接)
        #    这里必须使用 await，确保资源释放后再进行下一步
        await self.disconnect(user_id)

        # 2. 注册新连接
        self.active_connections[user_id] = websocket
        logger.info(f"🔌 [WS] User {user_id} connected")

        # 3. 为该用户启动独立的 MQ 监听任务
        #    不等待它完成 (create_task)，让它在后台跑
        task = asyncio.create_task(self.start_mq_listener(user_id, websocket))
        self.listening_tasks[user_id] = task

    async def disconnect(self, user_id: str):
        """
        断开连接并清理资源
        使用 .pop(key, None) 防止 KeyError
        """
        # 1. 取消后台监听任务
        task = self.listening_tasks.pop(user_id, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass  # 正常退出

        # 2. 关闭 MQ Channel
        channel = self.mq_channels.pop(user_id, None)
        if channel and not channel.is_closed:
            try:
                await channel.close()
            except Exception as e:
                logger.warning(f"⚠️ Error closing MQ channel for {user_id}: {e}")

        # 3. 关闭 WebSocket (如果还没关)
        websocket = self.active_connections.pop(user_id, None)
        if websocket:
            try:
                # 检查 socket 状态比较困难，通常直接 close，捕获异常即可
                await websocket.close()
            except Exception:
                pass  # 忽略早已关闭的连接错误

        logger.info(f"👋 [WS] User {user_id} resources cleaned up")

    async def start_mq_listener(self, user_id: str, websocket: WebSocket):
        """
        核心逻辑：每个 WebSocket 用户对应一个 MQ 队列
        """
        try:
            # 1. 获取一个新的 Channel (独立的)
            channel = await RabbitMQClient.get_new_channel()
            self.mq_channels[user_id] = channel

            # 2. 声明专属队列 (例如: user_2_inbox)
            #    auto_delete=True 表示连接断开后队列自动删除，不积压消息
            queue_name = f"user_{user_id}_inbox"
            queue = await channel.declare_queue(queue_name, auto_delete=True)

            # 3. 绑定路由 (例如: 发送给 notify.2 的消息会进这个队列)
            routing_key = f"notify.{user_id}"
            await queue.bind(exchange="pylab.direct", routing_key=routing_key)

            logger.info(f"👂 [WS-MQ] Listener started for {user_id} on key {routing_key}")

            # 4. 消费消息并转发给 WebSocket
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        # 解析消息
                        body = message.body.decode()
                        # print(f"📨 [WS Send] -> User {user_id}: {body}")

                        # 通过 WebSocket 发送给前端
                        # 注意：这里需要检查 ws 是否还活着
                        if websocket.client_state.value == 1:  # CONNECTED
                            await websocket.send_text(body)
                        else:
                            logger.warning(f"⚠️ User {user_id} WS closed, stopping listener")
                            break

        except asyncio.CancelledError:
            # 任务被取消 (用户断开连接时触发)
            pass
        except Exception as e:
            logger.error(f"❌ [WS-MQ Error] Listener failed for {user_id}: {e}")
            # 出错后触发断开清理
            await self.disconnect(user_id)

    async def send_personal_message(self, message: str, user_id: str):
        """(可选) 直接通过内存发送消息，不走 MQ"""
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)


# 全局单例
ws_manager = ConnectionManager()