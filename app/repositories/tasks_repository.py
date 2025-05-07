from sqlalchemy import select

from app.db.models import Task
from app.entity.filter import TaskFilter
from app.repositories.base_repository import SQLAlchemyRepository


class TaskRepository(SQLAlchemyRepository):
    model = Task

    async def get_tasks_filter(self, task_filter: TaskFilter):
        query = select(self.model)
        query = task_filter.filter(query)
        res = await self.session.execute(query)
        return res.scalars().all()
