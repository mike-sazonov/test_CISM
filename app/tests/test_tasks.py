import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

from app.api.dependencies import get_task_service
from app.entity.task import TaskCreate
from app.services.rabbit import RabbitProducer
from app.services.task import TaskService
from app.tests.conftest import UnitOfWorkTest, rabbit_service
from app.utils.unitofwork import IUnitOfWork
from main import app

client = TestClient(app)


async def get_task_service_test():
    return TaskService(UnitOfWorkTest(), rabbit_service)


class Test:
    app.dependency_overrides[get_task_service] = get_task_service_test

    @pytest.mark.asyncio
    async def test_create_task(self):
        data = TaskCreate(title="test title", description="test description")

        response = client.post("/api/v1/tasks/", json=data.model_dump())

        assert response.status_code == 201
