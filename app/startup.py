from sqlalchemy import create_engine, inspect
from .config import settings
from .db import Question


# Создание таблицы
def create_table():
    engine = create_engine(settings.db_url)
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    # Если таблица нет, то создаем
    if Question.__tablename__ not in existing_tables:
        Question.metadata.create_all(bind=engine)
