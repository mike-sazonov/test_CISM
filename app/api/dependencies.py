from fastapi import Depends, Request

from app.services.task import TaskService
from app.utils.unitofwork import IUnitOfWork, UnitOfWork


async def get_task_service(request: Request, uow: IUnitOfWork = Depends(UnitOfWork)):
    return TaskService(uow, request.app.state.rabbit_producer)
