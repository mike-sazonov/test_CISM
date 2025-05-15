from abc import ABC, abstractmethod

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.task import TaskOut


class AbstractRepository(ABC):
    @abstractmethod
    async def add_one(self, data: dict):
        raise NotImplementedError


class SQLAlchemyRepository(AbstractRepository):
    model = None

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_one(self, data: dict):
        stmt = insert(self.model).values(**data).returning(self.model)
        result = await self.session.execute(stmt)
        return TaskOut.model_validate(result.scalar_one())

    async def find_one(self, **filter_by):
        stmt = select(self.model).filter_by(**filter_by).with_for_update()
        result = await self.session.execute(stmt)
        instance = result.scalar_one_or_none()
        return TaskOut.model_validate(instance) if instance else None

    async def update_one(self, params: dict, **filter_by):
        stmt = (
            update(self.model)
            .values(**params)
            .filter_by(**filter_by)
            .returning(self.model)
        )
        await self.session.execute(stmt)
