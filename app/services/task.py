from app.entity.task import TaskCreate, TaskFromDB, TaskPriority
from app.utils.unitofwork import IUnitOfWork
from app.services.rabbit import RabbitService


class TaskService:
    def __init__(self, uow: IUnitOfWork, rabbit_service: RabbitService):
        self.uow = uow
        self.rabbit_service = rabbit_service

    async def publish_task(self, task: TaskFromDB):
        async with self.uow:
            await self.rabbit_service.publish(
                routing_key="task.created",
                message_body={
                    "task_id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "created_at": task.created_at.isoformat(),
                },
                priority=TaskPriority(task.priority).numeric
            )
            await self.uow.task.update_one({"status": "PENDING"}, id=task.id)
            await self.uow.commit()


    async def create_task(self, task: TaskCreate):
        cur_dict: dict = task.model_dump()

        async with self.uow:
            task_from_db = await self.uow.task.add_one(cur_dict)
            task = TaskFromDB.model_validate(task_from_db)

            await self.uow.commit()
            await self.publish_task(task)
