from app.db.models import Task
from app.repositories.base_repository import SQLAlchemyRepository


class TaskRepository(SQLAlchemyRepository):
    model = Task