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
    def __init__(
        self,
        rabbitmq_url: str,
        exchange_name: str = "tasks",
        queue_name: str = "task_queue",
    ):
        self.rabbitmq_url = rabbitmq_url
        self.exchange_name = exchange_name
        self.queue_name = queue_name
        self.connection: RobustConnection | None = None
        self.channel: RobustChannel | None = None
        self.exchange = None

    async def connect(self):
        self.connection = await connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()

        self.exchange = await self.channel.declare_exchange(
            self.exchange_name,
            ExchangeType.TOPIC,
            durable=True,
        )

        arguments = {"x-max-priority": 10}
        queue = await self.channel.declare_queue(
            self.queue_name,
            durable=True,
            arguments=arguments,
        )

        await queue.bind(self.exchange, routing_key="task.*")

    async def publish(
        self, routing_key: str, message_body: dict[str, Any], priority: int
    ):
        if not self.exchange:
            raise RuntimeError(
                "RabbitPublisher is not connected. Call connect() first."
            )

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
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
