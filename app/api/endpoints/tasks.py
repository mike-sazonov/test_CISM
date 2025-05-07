from fastapi import APIRouter, Depends

from app.api.dependencies import get_task_service
from app.entity.task import TaskCreate
from app.services.task import TaskService

tasks_router = APIRouter(
    prefix="/api/v1/tasks"
)


@tasks_router.post('/')
async def create_task(task_data: TaskCreate, task_service: TaskService = Depends(get_task_service)):
    await task_service.create_task(task_data)
