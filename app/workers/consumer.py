import asyncio
import json
from datetime import datetime, timezone

from aio_pika import IncomingMessage, RobustChannel, RobustConnection, connect_robust

from app.core.config import settings
from app.core.logger import logger
from app.entity.task import TaskStatus
from app.utils.unitofwork import IUnitOfWork, UnitOfWork


class TaskWorker:
    def __init__(self, rabbitmq_url: str, uow: IUnitOfWork = UnitOfWork(), queue_name: str = "task_queue"):
        self.rabbitmq_url = rabbitmq_url
        self.uow = uow
        self.queue_name = queue_name
        self.connection: RobustConnection | None = None
        self.channel: RobustChannel | None = None
        self.queue = None


    async def connect(self):
        self.connection = await connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()
        self.queue = await self.channel.declare_queue(self.queue_name, durable=True, arguments={'x-max-priority': 10})


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
                await self.uow.commit()

                try:
                    task = await self.uow.task.find_one(id=task_id)
                    if not task:
                        return

                    await asyncio.sleep(2)

                    task.result = "task completed"
                    task.status = TaskStatus.COMPLETED
                    task.finished_at = datetime.now(timezone.utc)
                    await self.uow.commit()
                    logger.info(f"Task {task_id} completed")

                except Exception as e:
                    print(str(e))
                    logger.exception(f"Task {task_id} failed: {e}")
                    if task:
                        task.error = f"error: {e.__class__}"
                        task.status = TaskStatus.FAILED
                        task.finished_at = datetime.now(timezone.utc)
                        await self.uow.commit()


    async def start(self):
        await self.connect()
        logger.info("Worker is up")

        await self.queue.consume(self.handle_message)

        while True:
            await asyncio.sleep(1)

async def run_worker():
    worker = TaskWorker(rabbitmq_url=settings.RABBITMQ_URL)
    await worker.start()
