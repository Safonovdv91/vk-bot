from aiohttp.web_exceptions import HTTPBadRequest
from aiohttp_apispec import (
    docs,
    querystring_schema,
    request_schema,
    response_schema,
)
from aiohttp_cors import CorsViewMixin

from app.quiz.models import Answer
from app.quiz.schemes import (
    QuestionIdSchema,
    QuestionListSchema,
    QuestionPatchRequestsSchema,
    QuestionSchema,
    ThemeIdSchema,
    ThemeListQuerySchema,
    ThemeListSchema,
    ThemeQueryIdSchema,
    ThemeSchema,
)
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response


class ThemeAddView(AuthRequiredMixin, View, CorsViewMixin):
    @docs(
        tags=["Quiz"],
        summary="Добавление темы",
        description="Здесь добавляется тема",
    )
    @request_schema(ThemeSchema)
    @response_schema(ThemeSchema)
    async def post(self):
        title = self.data.get("title")
        description = self.data.get("description")
        theme = await self.store.quizzes.create_theme(title, description)

        return json_response(data=ThemeSchema().dump(theme))


class ThemeListView(AuthRequiredMixin, View, CorsViewMixin):
    @docs(tags=["Quiz"], summary="Отобразить темы")
    @querystring_schema(ThemeListQuerySchema)
    @response_schema(ThemeListSchema)
    async def get(self):
        limit = self.request.query.get("limit")
        offset = self.request.query.get("offset")
        themes = await self.store.quizzes.get_themes_list(limit, offset)

        return json_response(data=ThemeListSchema().dump({"themes": themes}))


class ThemeDeleteByIdView(AuthRequiredMixin, View, CorsViewMixin):
    @docs(tags=["Quiz"], summary="Удалить тему по ID")
    @querystring_schema(ThemeIdSchema)
    @response_schema(ThemeSchema)
    async def delete(self):
        theme_id = self.request.query.get("theme_id")

        theme = await self.store.quizzes.delete_theme_by_id(int(theme_id))

        if theme is None:
            raise HTTPBadRequest(
                reason=f"Темы с ID = {theme_id} не существует."
            )

        return json_response(
            data={
                "status": "deleted",
                "theme": ThemeSchema().dump(theme),
            }
        )


class QuestionAddView(AuthRequiredMixin, View, CorsViewMixin):
    @docs(tags=["Quiz"], summary="Добавить вопрос")
    @request_schema(QuestionSchema)
    @response_schema(QuestionSchema)
    async def post(self):
        theme_id = self.data.get("theme_id")
        raw_answers = self.data.get("answers")
        title = self.data.get("title")
        answers = [
            Answer(title=answer_raw["title"], score=answer_raw["score"])
            for answer_raw in raw_answers
        ]

        question = await self.store.quizzes.create_question(
            theme_id=theme_id, answers=answers, title=title
        )

        return json_response(data=QuestionSchema().dump(question))


class QuestionGetByIdView(AuthRequiredMixin, View, CorsViewMixin):
    @docs(tags=["Quiz"], summary="Получить вопрос по id")
    @querystring_schema(QuestionIdSchema)
    @response_schema(QuestionSchema)
    async def get(self):
        question_id = self.request.query.get("question_id")
        question = await self.store.quizzes.get_question_by_id(int(question_id))

        return json_response(data=QuestionSchema().dump(question))


class QuestionDeleteByIdView(AuthRequiredMixin, View, CorsViewMixin):
    @docs(tags=["Quiz"], summary="Удалить вопрос по ID")
    @querystring_schema(QuestionIdSchema)
    @response_schema(QuestionSchema)
    async def delete(self):
        question_id = self.request.query.get("question_id")
        question = await self.store.quizzes.delete_question_by_id(
            int(question_id)
        )

        return json_response(
            data={
                "status": "deleted",
                "question": QuestionSchema().dump(question),
            }
        )


class QuestionListView(AuthRequiredMixin, View, CorsViewMixin):
    @docs(tags=["Quiz"], summary="Отобразить список вопросов")
    @querystring_schema(ThemeQueryIdSchema)
    @response_schema(QuestionListSchema)
    async def get(self):
        theme_id = self.request.query.get("theme_id")
        limit = self.request.query.get("limit")
        offset = self.request.query.get("offset")
        questions = await self.store.quizzes.get_questions_list(
            theme_id, offset, limit
        )

        return json_response(
            data=QuestionListSchema().dump({"questions": questions})
        )


class QuestionPatchById(AuthRequiredMixin, View, CorsViewMixin):
    @docs(
        tags=["Quiz"],
        summary="Изменить вопрос по ID",
        description="Изменить существубщий вопрос, "
        "можно изменить title и id темы.",
    )
    @querystring_schema(QuestionIdSchema)
    @request_schema(QuestionPatchRequestsSchema)
    @response_schema(QuestionSchema)
    async def patch(self):
        question_id = self.request.query.get("question_id")
        raw_answers = self.data.get("answers")
        theme_id = self.data.get("theme_id")
        title = self.data.get("title")

        if raw_answers:
            answers = [
                Answer(title=answer_raw["title"], score=answer_raw["score"])
                for answer_raw in raw_answers
            ]
        else:
            answers = None

        question = await self.store.quizzes.update_question(
            question_id=int(question_id),
            new_theme_id=theme_id,
            new_title=title,
            new_answers=answers,
        )

        return json_response(data=QuestionSchema().dump(question))
