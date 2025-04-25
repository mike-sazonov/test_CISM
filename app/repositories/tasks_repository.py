from app.repositories.base_repository import SQLAlchemyRepository
from app.db.models import Task


class TaskRepository(SQLAlchemyRepository):
    model = Task