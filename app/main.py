import logging
from datetime import datetime, timedelta, timezone

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .db import Question, SessionLocal
from .startup import create_table

# Получение пользовательского логгера и установка уровня логирования
main_logger = logging.getLogger(__name__)
main_logger.setLevel(logging.INFO)

# Настройка обработчика и форматировщика
main_handler = logging.FileHandler(f"{__name__}.log", mode='w')
main_formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")

# добавление форматировщика к обработчику
main_handler.setFormatter(main_formatter)

# добавление обработчика к логгеру
main_logger.addHandler(main_handler)

# URL для получения вопросов
API_URL = "https://jservice.io/api/"

# Максимальное число запросов
QUESTIONS_LIMIT = 10

# Максимальное число повторных запросов для получения вопросов
MAX_REQUEST = 5

app = FastAPI()


# Модель для входящего запроса
class QuestionRequest(BaseModel):
    questions_number: int = Field(..., gt=0)


@app.post("/questions")
def get_questions(request: QuestionRequest):
    # Объявляем контекст
    context = {}

    # Проверяем допустимость количества запросов
    questions_numbers = request.questions_number

    # Ограничиваем число запросов
    if questions_numbers > QUESTIONS_LIMIT:
        questions_numbers = QUESTIONS_LIMIT
        main_logger.info(f"Limit questions number: {QUESTIONS_LIMIT}, request with: {request.questions_number}."
                         f"Requests are limited to {questions_numbers}")

    # Получаем вопросы от внешнего API
    questions = api_questions(questions_numbers)
    main_logger.info(f"Call question_last with {request.questions_number}")

    try:
        # Устанавливаем соединение с бд
        with SessionLocal() as session:

            # Получаем последний сохраненный вопрос
            question_last = session.query(Question).order_by(Question.id.desc()).first()

            # Проверяем наличие ответа
            if question_last is not None:

                # Формируем контекст
                context = {
                    "id": question_last.id,
                    "question_id": question_last.question_id,
                    "question_text": question_last.question_text,
                    "question_text_answer": question_last.question_text_answer,
                    "question_date": question_last.question_date,
                    "question_date_created": question_last.question_date_created,
                }
                main_logger.info(f"Confirm context for question id: {question_last.id}")
            else:
                main_logger.info("No questions in database")

            # Список id из ответа api
            questions_ids = [question['id'] for question in questions]

            # Счетчик запросов к стороннему api
            count_retry = 0

            # количество вопросов
            questions_count = len(questions_ids)

            # проверенные вопросы
            questions_checks = set()

            # пока не достигнуто максимальное число запросов или не получены все уникальные вопросы
            while MAX_REQUEST > count_retry and questions_count > 0:

                # Проверяем уникальность вопросы
                for question_id in questions_ids:

                    # Если уже проверяли этот вопрос
                    if question_id in questions_checks:
                        break

                    # Добавляем вопрос в проверенные
                    questions_checks.add(question_id)

                    # Пытаемся найти вопрос в базе
                    question_base = session.query(Question).filter_by(question_id=question_id).first()

                    # Если вопрос уникальный
                    if question_base is None:

                        # Сохраняем вопрос
                        for question in questions:
                            if question.get("id") == question_id:
                                question_save = Question(
                                    question_id=question['id'],
                                    question_text=question['question'],
                                    question_text_answer=question['answer'],
                                    question_date_created=datetime.now(timezone(timedelta(hours=3))),
                                    question_date=question['created_at'],
                                )
                                session.add(question_save)
                                main_logger.info(f"Save unique question: {question_id}")

                                # Уменьшаем количество ответов
                                questions_count -= 1

                                break
                    else:
                        main_logger.info(f"Find not unique questions_id: {question_id}")

                # Если есть не уникальные вопросы
                if questions_count > 0:

                    # увеличиваем число повторных запросов
                    count_retry += 1

                    # Повторно запрашиваем ответы
                    questions = api_questions(len(questions_count))
                    main_logger.info(f"Retry to get unique {len(questions_count)} question(s)")

            # Сохраняем данные
            session.commit()
            main_logger.info("Commit question(s)")

            return context

    except Exception as e:
        main_logger.exception(f"Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        SessionLocal.close_all()


def api_questions(quantity: int):
    # Запрашиваем новые вопросы с публичного API
    url = API_URL + f"random?count={quantity}"
    try:
        response = requests.get(url, timeout=5)
        # Проверяем статус код ответа
        if response.status_code != 200:
            main_logger.exception("Exception: Failed to fetch questions from the API")
            raise HTTPException(status_code=500, detail="Failed to fetch questions from the API")
    except requests.Timeout:
        main_logger.exception("Exception: Gateway Timeout in request to API")
        raise HTTPException(status_code=504, detail="Gateway Timeout")

    main_logger.info("Return response from API")
    return response.json()


@app.get("/")
def read_root():
    return {"Приложение Вопросы": "Принимает post запрос по /questions с json {questions_num: <int>} "
                                  "Получает от стороннего api questions_num число ответов для викторины. "
                                  "Возвращает json с последним вопросом и ответом от предыдущего запроса"
            }


@app.on_event("startup")
def startup():
    main_logger.info("Start app")
    create_table()
    main_logger.info("Create tables")


@app.on_event("shutdown")
def shutdown():
    main_logger.info("Shutdown app")
    SessionLocal.close_all()
    main_logger.info("Close all sessions")
