from sqlalchemy import select

from app.db.models import Task
from app.entity.filter import TaskFilter #?тут просто фильтр
from app.repositories.base_repository import SQLAlchemyRepository


class TaskRepository(SQLAlchemyRepository):
    model = Task

    async def get_filter(self, task_filter: TaskFilter): # нейминг
        query = select(self.model)
        query = task_filter.filter(query)
        res = await self.session.execute(query)
        return res.scalars().all()
