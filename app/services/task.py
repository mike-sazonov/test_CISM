from app.entity.task import Task, TaskCreate, TaskPriority, TaskStatus
from app.services.rabbit import RabbitService
from app.utils.unitofwork import IUnitOfWork


class TaskService:
    def __init__(self, uow: IUnitOfWork, rabbit_service: RabbitService):
        self.uow = uow
        self.rabbit_service = rabbit_service

    async def publish_task(self, task: Task):
        async with self.uow:
            await self.uow.task.update_one({"status": TaskStatus.PENDING}, id=task.id)
            await self.rabbit_service.publish(
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
