import asyncio

from app.core.config import settings
from app.services.rabbit import RabbitConsumer


async def run_worker():
    worker = RabbitConsumer(rabbitmq_url=settings.RABBITMQ_URL)
    await worker.start()


if __name__ == "__main__":
    asyncio.run(run_worker())
