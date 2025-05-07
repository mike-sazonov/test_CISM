import json
from typing import Any

from aio_pika import (
    ExchangeType,
    Message,
    RobustChannel,
    RobustConnection,
    connect_robust,
)


class RabbitService:
    def __init__(self, rabbitmq_url: str, exchange_name: str = "tasks", queue_name: str = "task_queue"):
        self.rabbitmq_url = rabbitmq_url
        self.exchange_name = exchange_name
        self.queue_name = queue_name
        self.connection: RobustConnection | None = None
        self.channel: RobustChannel | None = None
        self.exchange = None

    async def connect(self):
        """Подключение к RabbitMQ и создание обменника и очереди с приоритетами."""
        self.connection = await connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()

        # Создаем обменник
        self.exchange = await self.channel.declare_exchange(
            self.exchange_name,
            ExchangeType.TOPIC,
            durable=True,
        )

        # Создаем очередь с поддержкой приоритета
        arguments = {"x-max-priority": 10}
        queue = await self.channel.declare_queue(
            self.queue_name,
            durable=True,
            arguments=arguments,
        )

        # Биндим очередь к обменнику
        await queue.bind(self.exchange, routing_key="task.*")


    async def publish(self, routing_key: str, message_body: dict[str, Any], priority: int):
        """Публикация сообщения с учетом приоритета."""
        if not self.exchange:
            raise RuntimeError("RabbitPublisher is not connected. Call connect() first.")

        message = Message(
            body=json.dumps(message_body).encode(),
            content_type="application/json",
            delivery_mode=2,  # persistent
            priority=priority,
        )

        await self.exchange.publish(
            message,
            routing_key=routing_key,
        )

    async def close(self):
        """Закрытие соединения."""
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()