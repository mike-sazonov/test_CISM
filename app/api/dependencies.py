from fastapi import Depends, Request

from app.utils.unitofwork import UnitOfWork, IUnitOfWork
from app.services.task import TaskService


async def get_task_service(request: Request, uow: IUnitOfWork = Depends(UnitOfWork)):
    return TaskService(uow, request.app.state.rabbit_service)