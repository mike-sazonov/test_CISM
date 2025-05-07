import math

from app.entity.filter import TaskFilter
from app.entity.task import TaskCreate, TaskFromDB, TaskPriority
from app.services.rabbit import RabbitService
from app.utils.unitofwork import IUnitOfWork


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


    async def get_all_tasks(self, task_filter: TaskFilter, page: int, size: int):
        offset_min = page * size
        offset_max = (page + 1) * size
        async with self.uow:
            tasks = await self.uow.task.get_tasks_filter(task_filter)
            response = tasks[offset_min:offset_max] + [
                {
                    "page": page,
                    "size": size,
                    "total": math.ceil(len(tasks) / size) - 1,
                }
            ]
            return response