from fastapi import Depends, HTTPException, status

from app.api.schemas.task import TaskCreate, TaskFromDB, TaskStatusOut
from app.utils.unitofwork import UnitOfWork, IUnitOfWork
from app.services.rabbit_publisher import RabbitPublisher
from app.db.models import TaskPriority


class TaskService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    async def publish_task(self, task: TaskFromDB, rabbit_publisher: RabbitPublisher):
        try:
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
            await self.uow.task.update_one({"status": "PENDING"}, id=task.id)
            await self.uow.commit()
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


    async def create_task(self, task: TaskCreate, rabbit_publisher: RabbitPublisher):
        cur_dict: dict = task.model_dump()

        async with self.uow:
            task_from_db = await self.uow.task.add_one(cur_dict)
            task = TaskFromDB.model_validate(task_from_db)

            await self.uow.commit()
            await self.publish_task(task, rabbit_publisher)


    async def check_tasks(self, rabbit_publisher: RabbitPublisher):
        not_pending_tasks = await self.uow.task.find_filter(status="NEW")
        if not_pending_tasks:
            for task in not_pending_tasks:
                await self.publish_task(task, rabbit_publisher)


async def get_task_service(uow: IUnitOfWork = Depends(UnitOfWork)):
    return TaskService(uow)
