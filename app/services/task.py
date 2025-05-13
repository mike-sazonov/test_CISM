import math
from uuid import UUID

from fastapi import HTTPException, status

from app.entity.filter import TaskFilter
from app.entity.task import TaskCreate, TaskFromDB, TaskPriority, TaskStatus
from app.services.rabbit import RabbitService
from app.utils.unitofwork import IUnitOfWork


class TaskService:
    def __init__(self, uow: IUnitOfWork, rabbit_service: RabbitService):
        self.uow = uow
        self.rabbit_service = rabbit_service

    async def publish_task(self, task: TaskFromDB):
        async with self.uow:
            await self.uow.task.update_one({"status": TaskStatus.PENDING}, id=task.id)
            await self.uow.commit()
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


    async def create_task(self, task: TaskCreate):
        cur_dict: dict = task.model_dump()

        async with self.uow:
            task_from_db = await self.uow.task.add_one(cur_dict)
            task = TaskFromDB.model_validate(task_from_db)

            await self.uow.commit()
            await self.publish_task(task)


    async def get_task(self, task_id: UUID):
        async with self.uow:
            task = await self.uow.task.find_one(id=task_id)
            return task


    async def get_task_status(self, task_id: UUID):
        async with self.uow:
            task = await self.uow.task.find_one(id=task_id)

            if not task:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND, detail='Task not found'
                )

            return task.status


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


    async def cancel_task(self, task_id: UUID):
        async with self.uow:
            task = await self.uow.task.find_one(id=task_id)

            if not task:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND, detail='Task not found'
                )

            if task.status not in (TaskStatus.NEW, TaskStatus.PENDING):
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, detail='Task in wrong status for cancelling'
                )

            await self.uow.task.update_one({"status": TaskStatus.CANCELLED}, id=task_id)
            await self.uow.commit()
