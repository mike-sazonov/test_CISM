import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_task_service
from app.entity.task import TaskCreate
from app.services.task import TaskService
from app.tests.conftest import MockRabbitProducer, UnitOfWorkTest
from app.utils.unitofwork import UnitOfWork
from main import app

client = TestClient(app)


async def get_test_task_service():
    return TaskService(UnitOfWorkTest(), MockRabbitProducer("url"))


app.dependency_overrides[get_task_service] = get_test_task_service
app.dependency_overrides[UnitOfWork] = UnitOfWorkTest

data = TaskCreate(title="test title", description="test description")


@pytest.mark.asyncio
async def test_create_task():
    response = client.post("/api/v1/tasks/", json=data.model_dump())
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_get_tasks_limit():
    for _ in range(10):
        client.post("/api/v1/tasks/", json=data.model_dump())

    response = client.get("/api/v1/tasks/", params={"limit": 10, "offset": 0})
    tasks = response.json()

    assert len(tasks) == 10
    assert all(task["title"] == "test title" for task in tasks)


@pytest.mark.asyncio
async def test_get_task_by_id():
    tasks = client.get("/api/v1/tasks/", params={"limit": 1, "offset": 0})
    task_id = tasks.json()[0]["id"]
    response = client.get(f"api/v1/tasks/{task_id}")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_task_by_invalid_id():
    invalid_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"api/v1/tasks/{invalid_id}")

    assert response.status_code == 404
    assert response.json() == {'detail': 'Task not found'}


@pytest.mark.asyncio
async def test_get_task_not_uuid():
    response = client.get(f"api/v1/tasks/{"random_string"}")

    assert response.status_code == 422