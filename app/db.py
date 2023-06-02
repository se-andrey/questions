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
    question_id: int
    question_text: str
    question_text_answer: str
    question_date_created: Optional[datetime] = None
    question_date: Optional[datetime] = None


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer)
    question_text = Column(Text)
    question_text_answer = Column(Text)
    question_date_created = Column(DateTime)
    question_date = Column(DateTime)


engine = sqlalchemy.create_engine(settings.db_url)
metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
