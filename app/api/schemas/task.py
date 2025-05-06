from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from app.db.models import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    title: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM


class TaskFromDB(BaseModel):
    id: UUID
    title: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: str | None = None
    error: str | None = None

    model_config = {'from_attributes': True}


class TaskStatusOut(BaseModel):
    status: TaskStatus
    id: UUID

    model_config = {'from_attributes': True}
