from aiohttp.web_exceptions import HTTPBadRequest, HTTPConflict, HTTPNotFound
from aiohttp_apispec import querystring_schema, request_schema, response_schema

from app.quiz.models import Answer
from app.quiz.schemes import (
    ListQuestionSchema,
    QuestionIdSchema,
    QuestionSchema,
    ThemeIdSchema,
    ThemeListSchema,
    ThemeSchema,
)
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response


class ThemeAddView(AuthRequiredMixin, View):
    @request_schema(ThemeSchema)
    @response_schema(ThemeSchema)
    async def post(self):
        title = self.data.get("title")
        description = self.data.get("description")
        if await self.store.quizzes.get_theme_by_title(title):
            raise HTTPConflict
        theme = await self.store.quizzes.create_theme(title, description)

        return json_response(data=ThemeSchema().dump(theme))


class ThemeListView(AuthRequiredMixin, View):
    @response_schema(ThemeListSchema)
    async def get(self):
        themes = await self.store.quizzes.list_themes()

        return json_response(data=ThemeListSchema().dump({"themes": themes}))


class QuestionAddView(AuthRequiredMixin, View):
    @request_schema(QuestionSchema)
    @response_schema(QuestionSchema)
    async def post(self):
        theme_id = self.data["theme_id"]
        raw_answers = self.data["answers"]
        title = self.data["title"]

        if len(raw_answers) < 2:
            raise HTTPBadRequest

        if await self.store.quizzes.get_theme_by_title(title):
            raise HTTPConflict

        if not await self.store.quizzes.get_theme_by_id(theme_id):
            raise HTTPNotFound

        answers = [
            Answer(title=answer_raw["title"], score=answer_raw["score"])
            for answer_raw in raw_answers
        ]

        if len(answers) < 2:
            raise HTTPBadRequest(reason="Слишком мало вопросов")

        answers_scores = sum(answer.score for answer in answers)
        if answers_scores != 100:
            raise HTTPBadRequest(
                reason=f"Общее количество очков за ответы должно быть = 100,"
                f" передано : {answers_scores}"
            )

        question = await self.store.quizzes.create_question(
            theme_id=theme_id, answers=answers, title=title
        )
        return json_response(data=QuestionSchema().dump(question))


class QuestionGetByIdView(AuthRequiredMixin, View):
    @querystring_schema(QuestionIdSchema)
    @response_schema(QuestionSchema)
    async def get(self):
        question_id = int(self.request.query.get("question_id"))
        question = await self.store.quizzes.get_question_by_id(question_id)

        return json_response(data=QuestionSchema().dump(question))


class QuestionDeleteByIdView(AuthRequiredMixin, View):
    @querystring_schema(QuestionIdSchema)
    @response_schema(QuestionSchema)
    async def delete(self):
        question_id = self.request.query.get("question_id")
        question = await self.store.quizzes.delete_question_by_id(question_id)
        if question is None:
            raise HTTPBadRequest(
                reason=f"Вопроса с ID = {question_id} не существует."
            )

        return json_response(
            data={
                "status": "deleted",
                "question": QuestionSchema().dump(question),
            }
        )


class QuestionListView(AuthRequiredMixin, View):
    @querystring_schema(ThemeIdSchema)
    @response_schema(ListQuestionSchema)
    async def get(self):
        theme_id = self.request.query.get("theme_id")
        questions = await self.store.quizzes.list_questions(theme_id)

        return json_response(
            data=ListQuestionSchema().dump({"questions": questions})
        )
