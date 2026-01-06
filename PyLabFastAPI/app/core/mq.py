import json
import logging
from aio_pika import connect_robust, Message, DeliveryMode, IncomingMessage
from app.config import settings

logger = logging.getLogger(__name__)


class RabbitMQClient:
    connection = None
    channel = None
    # 定义队列名称，必须唯一
    QUEUE_NAME = "pylab_course_sync_queue"

    @classmethod
    async def init(cls):
        """初始化 RabbitMQ 连接"""
        if not cls.connection:
            # connect_robust 支持断线自动重连，生产环境必备
            try:
                cls.connection = await connect_robust(settings.RABBITMQ_URL)
                cls.channel = await cls.connection.channel()

                # 声明队列 (durable=True 表示持久化，重启 MQ 队列不丢)
                await cls.channel.declare_queue(cls.QUEUE_NAME, durable=True)
                logger.info("🐰 [RabbitMQ] 连接成功，队列已就绪")
            except Exception as e:
                logger.error(f"❌ [RabbitMQ] 连接失败: {e}")
                raise e

    @classmethod
    async def close(cls):
        """关闭连接"""
        if cls.connection:
            await cls.connection.close()
            logger.info("🛑 [RabbitMQ] 连接已关闭")

    @classmethod
    async def publish(cls, message_body: dict):
        """生产者：发送消息到队列"""
        if not cls.channel:
            await cls.init()

        # 发送持久化消息
        await cls.channel.default_exchange.publish(
            Message(
                body=json.dumps(message_body).encode(),
                delivery_mode=DeliveryMode.PERSISTENT
            ),
            routing_key=cls.QUEUE_NAME
        )
        logger.info(f"📨 [MQ Send] 消息已入队: {message_body}")

    @classmethod
    async def consume(cls, callback_func):
        """消费者：启动监听"""
        if not cls.channel:
            await cls.init()

        queue = await cls.channel.declare_queue(cls.QUEUE_NAME, durable=True)

        # 内部处理包装器：负责解析消息和 ACK
        async def process_wrapper(message: IncomingMessage):
            async with message.process():  # 处理完自动发送 ACK 确认
                body = json.loads(message.body.decode())
                logger.info(f"📥 [MQ Recv] 收到消息: {body}")
                try:
                    # 调用真正的业务逻辑
                    await callback_func(body)
                except Exception as e:
                    logger.error(f"❌ [MQ Error] 消费失败: {e}")
                    # 可以在这里做死信队列逻辑，暂略

        # 启动消费 (prefetch_count=1 表示同一时间只处理 1 条，防止压垮后端)
        await cls.channel.set_qos(prefetch_count=1)
        await queue.consume(process_wrapper)
        logger.info("👀 [RabbitMQ] 消费者正在后台监听...")