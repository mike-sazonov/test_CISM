from fastapi import APIRouter, Depends, Request

from app.api.schemas.task import TaskCreate
from app.services.task_service import TaskService, get_task_service


tasks_router = APIRouter(
    prefix="/api/v1/tasks"
)


@tasks_router.post('/')
async def create_task(request: Request,
        task_data: TaskCreate,
        task_service: TaskService = Depends(get_task_service),
                      ):
    await task_service.create_task(task_data, request.app.state.rabbit_publisher)


