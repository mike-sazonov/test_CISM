from contextlib import asynccontextmanager

import uvicorn

from fastapi import FastAPI

from app.core.logger import logger
from app.core.config import settings
from app.api.endpoints.tasks import tasks_router
from app.services.rabbit_publisher import RabbitPublisher


rabbit_publisher: RabbitPublisher | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rabbit_publisher

    rabbit_publisher = RabbitPublisher(rabbitmq_url=settings.RABBITMQ_URL)
    await rabbit_publisher.connect()
    app.state.rabbit_publisher = rabbit_publisher
    logger.info("RabbitMQ connected")
    yield

    if rabbit_publisher and rabbit_publisher.connection and not rabbit_publisher.connection.is_closed:
        await rabbit_publisher.close()
        logger.info("RabbitMQ connect is close")


app = FastAPI(lifespan=lifespan)


app.include_router(tasks_router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run(app="main:app", reload=True)
