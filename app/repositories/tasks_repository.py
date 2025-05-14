from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy import select

from app.db.models import Task
from app.repositories.base_repository import SQLAlchemyRepository


class TaskRepository(SQLAlchemyRepository):
    model = Task

    async def get_filter(self, task: Filter):
        query = select(self.model)
        query = task.filter(query)
        res = await self.session.execute(query)
        return res.scalars().all()
