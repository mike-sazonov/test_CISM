from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.api.endpoints.tasks import tasks_router
from app.core.config import settings
from app.core.logger import logger
from app.services.rabbit import RabbitProducer


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.rabbit_producer = RabbitProducer(rabbitmq_url=settings.RABBITMQ_URL)
    await app.state.rabbit_producer.connect()
    logger.info("RabbitMQ connected")
    yield
    await app.state.rabbit_producer.close()
    logger.info("RabbitMQ connect is close")


app = FastAPI(lifespan=lifespan)

app.include_router(tasks_router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run(app="main:app", reload=True)
