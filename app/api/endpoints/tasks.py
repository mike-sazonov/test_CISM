import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_filter import FilterDepends

from app.api.dependencies import get_task_service
from app.entity.filter import TaskFilter
from app.entity.task import TaskCreate, TaskStatus
from app.services.task import TaskService
from app.utils.unitofwork import IUnitOfWork, UnitOfWork

tasks_router = APIRouter(prefix="/api/v1/tasks")


@tasks_router.post("/", status_code=201)
async def create_task(
    task_data: TaskCreate, task_service: TaskService = Depends(get_task_service)
):
    await task_service.create_task(task_data)


@tasks_router.get("/")
async def get_tasks(
    uow: IUnitOfWork = Depends(UnitOfWork),
    task_filter: TaskFilter = FilterDepends(TaskFilter),
    page: int = Query(ge=0, default=0),
    size: int = Query(ge=1, le=100),
):
    offset_min = page * size
    offset_max = (page + 1) * size

    async with uow:
        tasks = await uow.task.get_filter(task_filter)

    res = tasks[offset_min:offset_max] + [
        {
            "page": page,
            "size": size,
            "total": math.ceil(len(tasks) / size) - 1,
        }
    ]
    return res


@tasks_router.get("/{task_id}")
async def get_task(
    task_id: UUID,
    uow: IUnitOfWork = Depends(UnitOfWork),
):
    async with uow:
        task = await uow.task.find_one(id=task_id)

    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")

    return task


@tasks_router.delete("/{task_id}")
async def cancel_task(
    task_id: UUID,
    uow: IUnitOfWork = Depends(UnitOfWork),
):
    async with uow:
        task = await uow.task.find_one(id=task_id)

        if not task:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")

        if task.status not in (TaskStatus.NEW, TaskStatus.PENDING):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Task in wrong status for cancelling",
            )

        await uow.task.update_one({"status": TaskStatus.CANCELLED}, id=task_id)
        await uow.commit()


@tasks_router.get("/{task_id}/status")
async def get_task_status(
    task_id: UUID,
    uow: IUnitOfWork = Depends(UnitOfWork),
):
    async with uow:
        task = await uow.task.find_one(id=task_id)

    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")

    return task.status
