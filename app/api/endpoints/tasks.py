from fastapi import APIRouter, Depends, Query
from fastapi_filter import FilterDepends

from app.api.dependencies import get_task_service
from app.entity.filter import TaskFilter
from app.entity.task import TaskCreate
from app.services.task import TaskService

tasks_router = APIRouter(
    prefix="/api/v1/tasks"
)


@tasks_router.post('/')
async def create_task(task_data: TaskCreate, task_service: TaskService = Depends(get_task_service)):
    await task_service.create_task(task_data)

@tasks_router.get('/')
async def get_tasks(
        task_service: TaskService = Depends(get_task_service),
        task_filter: TaskFilter = FilterDepends(TaskFilter),
        page: int = Query(ge=0, default=0),
        size: int = Query(ge=1, le=100)):
    res = await task_service.get_all_tasks(task_filter, page, size)
    return res
