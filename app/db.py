from datetime import datetime
from typing import Optional

import sqlalchemy
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, Text
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

Base = declarative_base()
metadata = sqlalchemy.MetaData()


class QuestionCreate(BaseModel):
    id_question: int
    question_text: str
    answer_text: str
    created_date: Optional[datetime] = None
    date_question: Optional[datetime] = None


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    id_question = Column(Integer)
    question_text = Column(Text)
    answer_text = Column(Text)
    created_date = Column(DateTime)
    date_question = Column(DateTime)


engine = sqlalchemy.create_engine(settings.db_url)
metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
