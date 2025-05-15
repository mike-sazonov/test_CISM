import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from app.core.logger import logger
from app.entity.task import TaskStatus
from app.utils.unitofwork import IUnitOfWork, UnitOfWork

from aio_pika import (
    ExchangeType,
    Message,
    RobustChannel,
    RobustConnection,
    connect_robust,
    IncomingMessage
)


class RabbitService:
    def __init__(
        self,
        rabbitmq_url: str,
        queue_name: str = "task_queue",
    ):
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.connection: RobustConnection | None = None
        self.channel: RobustChannel | None = None

    async def connect(self):
        self.connection = await connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()


class RabbitProducer(RabbitService):
    def __init__(
        self,
        rabbitmq_url: str,
        queue_name: str = "task_queue",
        exchange_name: str = "tasks"
    ):
        super().__init__(rabbitmq_url, queue_name)
        self.exchange_name = exchange_name
        self.exchange = None

    async def connect(self):
        await super().connect()

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


class RabbitConsumer(RabbitService):
    def __init__(
        self,
        rabbitmq_url: str,
        queue_name: str = "task_queue",
        uow: IUnitOfWork = UnitOfWork()
    ):
        super().__init__(rabbitmq_url, queue_name)
        self.uow = uow
        self.queue = None

    async def connect(self):
        await super().connect()

        self.queue = await self.channel.declare_queue(
            self.queue_name, durable=True, arguments={"x-max-priority": 10}
        )

    async def handle_message(self, message: IncomingMessage):
        async with message.process():
            payload = json.loads(message.body)

            task_id = payload.get("task_id")
            if not task_id:
                logger.info("Received message without task_id")

            logger.info(f"Processed task {task_id}")
            await self.process_task(task_id)

    async def process_task(self, task_id: str):
        async with self.uow:
            task = await self.uow.task.find_one(id=task_id)
            if not task:
                logger.info(f"Task {task_id} not found")
                return

            if task.status != TaskStatus.PENDING:
                logger.info(f"Wrong status for task {task_id}")
                return

            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now(timezone.utc)
            await self.uow.task.update_one(task.model_dump(), id=task_id)
            await self.uow.commit()
        await self.complete_task(task_id)

    async def complete_task(self, task_id: str):
        async with self.uow:
            task = await self.uow.task.find_one(id=task_id)
            try:
                pass  # some work with task

            except Exception as e:
                logger.exception(f"Task {task_id} failed: {e}")
                task.error = f"error: {e.__class__}"
                task.status = TaskStatus.FAILED
            else:
                logger.info(f"Task {task_id} completed")
                task.result = "task completed"
                task.status = TaskStatus.COMPLETED
            finally:
                task.finished_at = datetime.now(timezone.utc)
                await self.uow.task.update_one(task.model_dump(), id=task_id)
                await self.uow.commit()

    async def start(self):
        await self.connect()
        logger.info("Worker is up")

        await self.queue.consume(self.handle_message)

        while True:
            await asyncio.sleep(1)
