from aiohttp.web_exceptions import HTTPBadRequest
from aiohttp_apispec import (
    docs,
    querystring_schema,
    request_schema,
    response_schema,
)

from app.blitz.schemes import (
    BlitzQuestionIdSchema as QuestionIdSchema,
    BlitzQuestionListSchema as QuestionListSchema,
    BlitzQuestionPatchRequestsSchema as QuestionPatchRequestsSchema,
    BlitzQuestionSchema as QuestionSchema,
    BlitzThemeIdSchema as ThemeIdSchema,
    BlitzThemeListQuerySchema as ThemeListQuerySchema,
    BlitzThemeListSchema as ThemeListSchema,
    BlitzThemeQueryIdSchema as ThemeQueryIdSchema,
    BlitzThemeSchema as ThemeSchema,
)
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response


class ThemeAddView(AuthRequiredMixin, View):
    @docs(
        tags=["Blitz"],
        summary="Добавление темы",
        description="Добавление тематики для будущих вопросов\n"
        " Указывается заголовок и описание",
    )
    @request_schema(ThemeSchema)
    @response_schema(ThemeSchema)
    async def post(self):
        title = self.data.get("title")
        description = self.data.get("description")
        theme = await self.store.blitzes.create_theme(title, description)

        return json_response(data=ThemeSchema().dump(theme))


class ThemeListView(AuthRequiredMixin, View):
    @docs(
        tags=["Blitz"],
        summary="Отобразить существующие темы",
        description="""
        Возвращает все существующие темы.
        """,
    )
    @querystring_schema(ThemeListQuerySchema)
    @response_schema(ThemeListSchema)
    async def get(self):
        limit = self.request.query.get("limit")
        offset = self.request.query.get("offset")
        themes = await self.store.blitzes.get_themes_list(limit, offset)

        return json_response(data=ThemeListSchema().dump({"themes": themes}))


class ThemeDeleteByIdView(
    AuthRequiredMixin,
    View,
):
    @docs(tags=["Blitz"], summary="Удалить тему по ID")
    @querystring_schema(ThemeIdSchema)
    @response_schema(ThemeSchema)
    async def delete(self):
        theme_id = self.request.query.get("theme_id")

        theme = await self.store.blitzes.delete_theme_by_id(int(theme_id))

        if theme is None:
            raise HTTPBadRequest(reason=f"Темы с ID = {theme_id} не существует.")

        return json_response(
            data={
                "status": "deleted",
                "theme": ThemeSchema().dump(theme),
            }
        )


class QuestionAddView(AuthRequiredMixin, View):
    @docs(
        tags=["Blitz"],
        summary="Добавить вопрос для игры блитз",
        description="""
        В одном вопросе несколько ответов.
        id темы - номер темы(если не указывать - то значение 1)
        title - заголовок вопроса(то что будут видеть игроки)
        answer - ответ на вопрос
        """,
    )
    @request_schema(QuestionSchema)
    @response_schema(QuestionSchema)
    async def post(self):
        # todo если тема не указана то дефолтное значение 1
        theme_id = self.data.get("theme_id")
        title = self.data.get("title")
        answer = self.data.get("answer")
        if theme_id is None:
            theme_id = 1

        question = await self.store.blitzes.create_question(
            theme_id=theme_id, answer=answer, title=title
        )

        return json_response(data=QuestionSchema().dump(question))


class QuestionGetByIdView(AuthRequiredMixin, View):
    @docs(
        tags=["Blitz"],
        summary="Получить вопрос по id",
        description="""
        Получить вопрос по id, если вопрос не найден - возвращается 404
        """,
    )
    @querystring_schema(QuestionIdSchema)
    @response_schema(QuestionSchema)
    async def get(self):
        question_id = self.request.query.get("question_id")
        question = await self.store.blitzes.get_question_by_id(int(question_id))

        return json_response(data=QuestionSchema().dump(question))


class QuestionDeleteByIdView(AuthRequiredMixin, View):
    @docs(
        tags=["Blitz"],
        summary="Удалить вопрос по ID",
        description="""
        Удалить вопрос по id, если вопрос не найден - возвращается 404
        """,
    )
    @querystring_schema(QuestionIdSchema)
    @response_schema(QuestionSchema)
    async def delete(self):
        question_id = self.request.query.get("question_id")
        question = await self.store.blitzes.delete_question_by_id(int(question_id))

        return json_response(
            data={
                "status": "deleted",
                "question": QuestionSchema().dump(question),
            }
        )


class QuestionListView(AuthRequiredMixin, View):
    @docs(
        tags=["Blitz"],
        summary="Отобразить список вопросов",
        description="""
        Отобразить список вопросов, если не указана тема -
        то отображаются все вопросы так же есть query поля
        limit и offset - для ограничения выборки
        """,
    )
    @querystring_schema(ThemeQueryIdSchema)
    @response_schema(QuestionListSchema)
    async def get(self):
        # todo если тема не указана то на данный момент выбрасывает ошибку
        # надо сделать чтобы слало просто все вопросы
        theme_id = self.request.query.get("theme_id")
        limit = self.request.query.get("limit")
        offset = self.request.query.get("offset")
        questions = await self.store.blitzes.get_questions_list(theme_id, offset, limit)

        return json_response(data=QuestionListSchema().dump({"questions": questions}))


class QuestionPatchById(AuthRequiredMixin, View):
    @docs(
        tags=["Blitz"],
        summary="Изменить вопрос по ID",
        description="""
        Изменяет существующий вопрос, для изменения необходимо передать
        question_id - в query параметре, остальные параметры передаются в 
        теле запроса
        """,
    )
    @querystring_schema(QuestionIdSchema)
    @request_schema(QuestionPatchRequestsSchema)
    @response_schema(QuestionSchema)
    async def patch(self):
        # todo Проверить валидацию по query т.к. в scheme ошибка
        question_id = self.request.query.get("question_id")
        theme_id = self.data.get("theme_id")
        title = self.data.get("title")
        answer = self.data.get("answer")

        question = await self.store.blitzes.update_question(
            question_id=int(question_id),
            new_theme_id=theme_id,
            new_title=title,
            new_answer=answer,
        )

        return json_response(data=QuestionSchema().dump(question))
