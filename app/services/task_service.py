from fastapi.exceptions import HTTPException

from app.api.schemas.task import TaskCreate, TaskFromDB, TaskStatusOut
from app.utils.unitofwork import IUnitOfWork
from app.services.rabbit_publisher import RabbitPublisher
from app.db.models import TaskPriority


class TaskService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    async def create_task(self, task: TaskCreate, rabbit_publisher: RabbitPublisher):
        cur_dict: dict = task.model_dump()

        async with self.uow:
            task_from_db = await self.uow.task.add_one(cur_dict)
            task = TaskFromDB.model_validate(task_from_db)

            await self.uow.commit()

        await rabbit_publisher.publish(
            routing_key="task.created",
            message_body={
                "task_id": str(task.id),
                "title": task.title,
                "description": task.description,
                "created_at": task.created_at.isoformat(),
            },
            priority=TaskPriority(task.priority).numeric
        )
