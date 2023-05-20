import sqlalchemy
from sqlalchemy import Column, Integer, Text
from sqlalchemy import DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

from datetime import datetime
from typing import Optional
from pydantic import BaseModel

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
