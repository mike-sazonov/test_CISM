from typing import Optional

from fastapi_filter.contrib.sqlalchemy import Filter

from app.db.models import Task
from app.entity.task import TaskStatus


class TaskFilter(Filter):
    status__in: Optional[list[TaskStatus]] = None

    class Constants(Filter.Constants):
        model = Task
