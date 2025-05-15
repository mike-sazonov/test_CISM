from app.entity.task import TaskOut, TaskCreate, TaskPriority, TaskStatus
from app.services.rabbit import RabbitProducer
from app.utils.unitofwork import IUnitOfWork


class TaskService:
    def __init__(self, uow: IUnitOfWork, rabbit_producer: RabbitProducer):
        self.uow = uow
        self.rabbit_producer = rabbit_producer

    async def publish_task(self, task: TaskOut):
        async with self.uow:
            await self.uow.task.update_one({"status": TaskStatus.PENDING}, id=task.id)
            await self.rabbit_producer.publish(
                routing_key="task.created",
                message_body={
                    "task_id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "created_at": task.created_at.isoformat(),
                },
                priority=TaskPriority(task.priority).numeric,
            )
            await self.uow.commit()

    async def create_task(self, task: TaskCreate):
        cur_dict: dict = task.model_dump()

        async with self.uow:
            task = await self.uow.task.add_one(cur_dict)
            await self.uow.commit()
            await self.publish_task(task)
