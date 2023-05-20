import requests

from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field
from .db import Question, SessionLocal
from .startup import create_table

app = FastAPI()


# Модель для входящего запроса
class QuestionRequest(BaseModel):
    questions_num: int = Field(..., gt=0)


@app.post("/questions")
def get_questions(request: QuestionRequest):
    # Получаем вопросы от внешнего API
    api_questions = get_quiz_from_api(request.questions_num)
    print(request.questions_num)
    # Устанавливаем соединение с бд
    with SessionLocal() as db:

        # Список id из ответа api
        id_list = [id_question['id'] for id_question in api_questions]

        # Список id всех сохраненных ранее вопросов
        id_in_base = [obj.id for obj in db.query(Question).all()]

        # id уникальных вопрос (еще не добавленных в бд)
        unic_ids = set(id_list) - set(id_in_base)

        # Пока не получили необходимое число уникальных ответов
        while len(unic_ids) != len(id_list):
            # Повторные id
            common_id = set(id_list) & set(id_in_base)

            # Удаляем повторые ответы
            api_questions = [item for item in api_questions if item['id'] not in common_id]
            id_list = [item for item in id_list if item not in common_id]

            # Повторно запрашиваем ответы
            temp_questions = get_quiz_from_api(len(common_id))

            # Добавляем полученные ответы к общим
            api_questions.extend(temp_questions)
            id_list.extend([id_question['id'] for id_question in temp_questions])

            # Обновляем id уникальных вопросов
            unic_ids = set(id_list) - set(id_in_base)

        # Сохраняем уникальные вопросы в базе данных
        for api_question in api_questions:
            question = Question(
                id_question=api_question['id'],
                question_text=api_question['question'],
                answer_text=api_question['answer'],
                created_date=datetime.now(timezone(timedelta(hours=3))),
                date_question=api_question['created_at'],
            )
            db.add(question)

        # Сохраняем данные
        db.commit()

        # Получаем последние сохраненные вопросы
        last_questions = db.query(Question).order_by(-Question.id).limit(request.questions_num + 1)

        # Проверяем были ли ответы до текущего запроса
        if (last_questions.count() - 1) < request.questions_num:
            return {"first_request": "no questions"}

        # Возвращаем последний сохраненный вопрос до последнего (текущего) запроса
        last_question = list(last_questions)[-1]
        return {
            "id_question": last_question.id,
            "question_text": last_question.question_text,
            "answer_text": last_question.answer_text,
            "date_question": last_question.date_question,
            "created_date": last_question.created_date,
        }


def get_quiz_from_api(quantity: int):
    # Запрашиваем новые вопросы с публичного API
    api_url = f"https://jservice.io/api/random?count={quantity}"
    response = requests.get(api_url)

    # Проверяем статус код ответа
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch questions from the API")
    return response.json()


@app.get("/")
def read_root():
    return {"Привет": "Это приложение принимает post запрос по /questions с json {questions_num: <int>} "
                      "Получает от стороннего api questions_num число ответов для викторины."
                      "Возвращает json с последним вопросом и ответом от предыдущего запроса"
            }


@app.on_event("startup")
def startup():
    create_table()


@app.on_event("shutdown")
def shutdown():
    SessionLocal.close_all()
