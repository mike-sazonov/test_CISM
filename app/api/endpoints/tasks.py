from fastapi import APIRouter, Depends, FastAPI, Request

from app.services.rabbit_publisher import RabbitPublisher
from app.api.schemas.task import TaskCreate, TaskFromDB
from app.services.task_service import TaskService
from app.utils.unitofwork import UnitOfWork, IUnitOfWork


tasks_router = APIRouter(
    prefix="/api/v1/tasks"
)


async def get_task_service(uow: IUnitOfWork = Depends(UnitOfWork)):
    return TaskService(uow)


@tasks_router.post('/')
async def create_task(request: Request,
        task_data: TaskCreate,
        task_service: TaskService = Depends(get_task_service),
                      ):
    return await task_service.create_task(task_data, request.app.state.rabbit_publisher)

