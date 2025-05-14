from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy import select

from app.db.models import Task
from app.entity.task import TaskOut
from app.repositories.base_repository import SQLAlchemyRepository


class TaskRepository(SQLAlchemyRepository):
    model = Task

    async def get_filter(self, task_filter: Filter, limit: int, offset: int):
        query = select(self.model)
        query = task_filter.filter(query)
        query = query.offset(offset).limit(limit)
        res = await self.session.execute(query)
        task_models = res.scalars().all()
        tasks = [TaskOut.model_validate(task_model) for task_model in task_models]
        return tasks
