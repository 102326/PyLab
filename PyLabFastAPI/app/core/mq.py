# PyLabFastAPI/app/core/mq.py
import json
import logging
import aio_pika
from aio_pika import connect_robust, Message, DeliveryMode, ExchangeType
from app.config import settings

logger = logging.getLogger("uvicorn")


class RabbitMQClient:
    """
    RabbitMQ 全局客户端 (单例模式 - 类方法实现)
    """
    connection: aio_pika.Connection = None
    channel: aio_pika.Channel = None
    EXCHANGE_NAME = "pylab.direct"  # 交换机名称

    @classmethod
    async def connect(cls):
        """初始化 RabbitMQ 连接"""
        if cls.connection and not cls.connection.is_closed:
            return

        try:
            # 1. 建立连接
            cls.connection = await connect_robust(settings.RABBITMQ_URL)

            # 2. 建立通道
            cls.channel = await cls.connection.channel()

            # 3. 声明交换机 (确保交换机存在)
            await cls.channel.declare_exchange(
                cls.EXCHANGE_NAME,
                ExchangeType.DIRECT,
                durable=True
            )
            logger.info("✅ [RabbitMQ] 连接成功 & 交换机已声明")
        except Exception as e:
            logger.error(f"❌ [RabbitMQ] 连接失败: {e}")
            raise e  # 抛出异常以便 main.py 捕获

    @classmethod
    async def close(cls):
        """关闭连接"""
        if cls.connection:
            await cls.connection.close()
            logger.info("🛑 [RabbitMQ] 连接已关闭")

    @classmethod
    async def publish(cls, routing_key: str, message: dict):
        """发送消息"""
        if not cls.channel or cls.channel.is_closed:
            await cls.connect()

        exchange = await cls.channel.get_exchange(cls.EXCHANGE_NAME)

        await exchange.publish(
            Message(
                body=json.dumps(message).encode(),
                delivery_mode=DeliveryMode.PERSISTENT
            ),
            routing_key=routing_key
        )

    # === [新增] 消费者监听方法 ===
    @classmethod
    async def consume(cls, queue_name: str, routing_key: str, callback_func):
        """
        启动消费者
        :param queue_name: 队列名称 (例如 'q_course_sync')
        :param routing_key: 绑定的路由键 (例如 'task.course.sync')
        :param callback_func: 处理消息的异步函数，接收 (data: dict)
        """
        if not cls.channel:
            await cls.connect()

        # 1. 声明队列 (持久化)
        queue = await cls.channel.declare_queue(queue_name, durable=True)

        # 2. 绑定队列到交换机
        await queue.bind(cls.EXCHANGE_NAME, routing_key=routing_key)

        # 3. 定义包装器 (处理消息确认和 JSON 解析)
        async def message_wrapper(message: aio_pika.IncomingMessage):
            async with message.process():  # 上下文管理器会自动 ack 消息
                try:
                    body = message.body.decode()
                    data = json.loads(body)
                    # 调用业务处理函数
                    await callback_func(data)
                except Exception as e:
                    logger.error(f"❌ [MQ Consume Error] 处理消息失败: {e}")
                    # 注意：message.process() 默认是 ack。
                    # 如果需要失败重试 (nack)，需要在这里手动处理，或使用死信队列。

        # 4. 开始消费 (不阻塞)
        await queue.consume(message_wrapper)
        logger.info(f"👂 [RabbitMQ] 正在监听队列: {queue_name} (Key: {routing_key})")

    @classmethod
    async def get_new_channel(cls) -> aio_pika.Channel:
        if not cls.connection or cls.connection.is_closed:
            await cls.connect()
        return await cls.connection.channel()