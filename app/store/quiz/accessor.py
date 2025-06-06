from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

import sqlalchemy.exc
from aiohttp.web_exceptions import (
    HTTPBadRequest,
    HTTPConflict,
    HTTPNotFound,
    HTTPServiceUnavailable,
)
from sqlalchemy import delete, func, update
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.base.base_accessor import BaseAccessor
from app.quiz.data import create_new_data
from app.quiz.models import (
    Answer,
    Question,
    Theme,
)
from app.vk.models import VkMessage
from tests.conftest import logger

if TYPE_CHECKING:
    from app.web.app import Application


class QuizAccessor(BaseAccessor):
    async def connect(self, app: "Application") -> None:
        self.logger.info("Подключаем QuizAccessor")

        if await self.get_theme_by_id(1) is None:
            self.logger.info("Создаем базовую тему.")
            await self.create_theme(title="default", description="default theme")

        count_questions = await self.get_questions_count(theme_id=1)
        logger.info("В базе %s вопросов", count_questions)

        if count_questions == 0:
            self.logger.info("В базовой теме нет вопросов, добавляем стандартные")
            for question in create_new_data():
                await self.create_question(
                    title=question.title,
                    theme_id=question.theme_id,
                    answers=question.answers,
                )

    async def create_theme(self, title: str, description: str | None = None) -> Theme:
        async with self.app.database.session() as session:
            theme = Theme(title=title, description=description)
            self.logger.info("Добавляем в базу данных %s", theme)

            try:
                session.add(theme)
                await session.commit()

            except sqlalchemy.exc.IntegrityError as exc:
                self.logger.exception(exc_info=exc, msg=exc)
                raise HTTPConflict(reason="Не удалось добавить тему") from exc

            except sqlalchemy.exc.InterfaceError as exc:
                self.logger.exception(exc_info=exc, msg=exc)
                raise HTTPServiceUnavailable from exc

            return theme

    async def get_theme_by_title(self, title: str) -> Theme | None:
        async with self.app.database.session() as session:
            title = await session.execute(select(Theme).where(Theme.title == title))

        return title.scalar_one_or_none()

    async def get_theme_by_id(self, id_: int) -> Theme | None:
        async with self.app.database.session() as session:
            theme = await session.execute(select(Theme).where(Theme.id == int(id_)))

        return theme.scalar_one_or_none()

    async def get_themes_list(
        self, limit: int | None = None, offset: int | None = None
    ) -> Sequence[Theme]:
        async with self.app.database.session() as session:
            stmt = select(Theme)

            if limit is not None:
                stmt = stmt.limit(limit)
            if offset is not None:
                stmt = stmt.offset(offset)

            result = await session.execute(stmt)

        return result.scalars().all()

    async def delete_theme_by_id(self, id_: int) -> Theme | None:
        async with self.app.database.session() as session:
            theme = await session.get(Theme, id_)

            if theme is None:
                raise HTTPBadRequest(reason="Темы с таким id не существует")
            try:
                await session.delete(theme)
                await session.commit()
            except sqlalchemy.exc.IntegrityError as exc:
                raise HTTPConflict(
                    reason="Нельзя удалить т.к. существуют" " вопросы принадлежащие теме"
                ) from exc
        return theme

    async def create_question(
        self, title: str, theme_id: int, answers: Iterable[Answer]
    ) -> Question:
        async with self.app.database.session() as session:
            question = Question(title=title, theme_id=theme_id, answers=answers)
            sum_score = sum(answer.score for answer in question.answers)

            if sum_score != 100:
                raise HTTPBadRequest(
                    reason=f"Сумма очков всех ответов должна быть равна 100, "
                    f"текущая сумма: {sum_score}"
                )

            try:
                session.add(question)
                await session.commit()

            except sqlalchemy.exc.IntegrityError as exc:
                self.logger.exception(exc_info=exc, msg=exc)
                raise HTTPBadRequest(reason="не удалось добавить вопрос") from exc

            except sqlalchemy.exc.InterfaceError as exc:
                self.logger.exception(exc_info=exc, msg=exc)
                raise HTTPServiceUnavailable from exc

        return question

    async def get_question_by_id(self, id_: int) -> Question | None:
        async with self.app.database.session() as session:
            result = await session.execute(
                select(Question)
                .where(Question.id == id_)
                .options(joinedload(Question.answers))
            )

        return result.unique().scalar_one_or_none()

    async def get_question_by_title(self, title: str) -> Question | None:
        stmt = (
            select(Question)
            .where(Question.title == title)
            .options(joinedload(Question.answers))
        )

        async with self.app.database.session() as session:
            return await session.scalar(stmt)

    async def get_questions_list(
        self,
        theme_id: int | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> Sequence[Question]:
        if theme_id is None:
            raise HTTPBadRequest

        stmt = (
            select(Question)
            .where(Question.theme_id == int(theme_id))
            .options(joinedload(Question.answers))
        )

        if limit:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)

        async with self.app.database.session() as session:
            questions = await session.scalars(stmt)

        questions = questions.unique().all()

        if len(questions) == 0:
            raise HTTPNotFound

        return questions

    async def delete_question_by_id(self, id_: int) -> Question | None:
        async with self.app.database.session() as session:
            try:
                question = (
                    await session.execute(
                        select(Question)
                        .where(Question.id == id_)
                        .options(joinedload(Question.answers))
                    )
                ).unique()
                question = question.scalar_one_or_none()

                if question is None:
                    raise HTTPBadRequest(
                        reason="Вопроса с таки id не существует," " или он был уже удален"
                    )
                stmt = delete(Answer).where(Answer.question_id == id_)
                await session.execute(stmt)

                stmt = delete(Question).where(Question.id == id_)
                await session.execute(stmt)

                await session.commit()

            except sqlalchemy.exc.IntegrityError as exc:
                await session.rollback()
                self.logger.exception(exc_info=exc, msg=exc)
                raise HTTPConflict(reason="Не удалось удалить вопрос") from exc

            except sqlalchemy.exc.InterfaceError as exc:
                await session.rollback()
                self.logger.exception(exc_info=exc, msg=exc)
                raise HTTPServiceUnavailable from exc

            else:
                self.logger.info("Вопрос с %s успешно удален", question.id)
                return question

    async def get_questions_count(self, theme_id: int | None = None) -> int:
        async with self.app.database.session() as session:
            try:
                if theme_id is None:
                    count_query = select(func.count()).select_from(Question)
                else:
                    count_query = (
                        select(func.count())
                        .select_from(Question)
                        .where(Question.theme_id == int(theme_id))
                    )
                result = await session.execute(count_query)

            except sqlalchemy.exc.InterfaceError as exc:
                self.logger.exception(exc_info=exc, msg=exc)
                raise HTTPServiceUnavailable from exc

            return result.scalar()

    async def update_question(
        self,
        question_id: int,
        new_title: str | None,
        new_theme_id: int | None,
        new_answers: Iterable[Answer] | None,
    ):
        async with self.app.database.session() as session:
            try:
                stmt = select(Question).where(Question.id == question_id)
                result = await session.execute(stmt)
                question = result.scalar_one_or_none()

                if not question:
                    raise HTTPBadRequest(reason="Вопрос не найден")

                stmt = update(Question).where(Question.id == question_id)
                if new_title:
                    stmt = stmt.values(title=new_title)
                if new_theme_id:
                    stmt = stmt.values(theme_id=new_theme_id)

                await session.execute(stmt)
                await session.commit()

            except (
                sqlalchemy.exc.IntegrityError,
                sqlalchemy.exc.ProgrammingError,
            ) as exc:
                self.logger.exception(exc_info=exc, msg=exc)
                await session.rollback()  # Откатываем транзакцию перед повторной попыткой
                raise HTTPBadRequest(
                    reason="Не удалось обновить вопрос из-за"
                    " проблемы целостности данных"
                ) from exc

            except sqlalchemy.exc.InterfaceError as exc:
                self.logger.exception(exc_info=exc, msg=exc)
                await session.rollback()  # Откатываем транзакцию перед повторной попыткой
                raise HTTPServiceUnavailable from exc


class VkMessageAccessor(BaseAccessor):
    async def connect(self, app: "Application") -> None:
        self.logger.info("Подключаем VKMessageAccessor")
        count_messages = await self.get_messages_count()
        logger.info("В базе %s сообщений", count_messages)

    async def add_message(self, conversation_id, text: str, user_id: int) -> VkMessage:
        async with self.app.database.session() as session:
            message: VkMessage = VkMessage(
                conversation_id=conversation_id,
                text=text,
                user_id=user_id,
            )
            self.logger.info("Добавляем в базу данных %s", message)

            try:
                session.add(message)
                await session.commit()

            except sqlalchemy.exc.IntegrityError as exc:
                self.logger.exception(exc_info=exc, msg=exc)
                raise HTTPConflict(reason="Не удалось добавить тему") from exc

            except sqlalchemy.exc.InterfaceError as exc:
                self.logger.exception(exc_info=exc, msg=exc)
                raise HTTPServiceUnavailable from exc

            except Exception as exc:
                self.logger.exception(exc_info=exc, msg=exc)
                raise HTTPServiceUnavailable from exc

            return message

    async def get_messages_count(self) -> int:
        async with self.app.database.session() as session:
            try:
                count_query = select(func.count()).select_from(VkMessage)
                result = await session.execute(count_query)

            except sqlalchemy.exc.InterfaceError as exc:
                self.logger.exception(exc_info=exc, msg=exc)
                raise HTTPServiceUnavailable from exc

            return result.scalar()

    async def get_messages_list(
        self,
        conversation_id: int | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ):
        if conversation_id is None:
            raise HTTPBadRequest(reason="Не указан идентификатор чата")

        stmt = select(VkMessage).where(VkMessage.conversation_id == int(conversation_id))

        if limit:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)
        try:
            async with self.app.database.session() as session:
                messages = await session.scalars(stmt)
        except Exception as exc:
            self.logger.exception(exc_info=exc, msg=exc)
            raise HTTPServiceUnavailable from exc

        vk_messages = messages.unique().all()

        if len(vk_messages) == 0:
            raise HTTPNotFound

        return vk_messages

    async def get_conversations_list(
        self,
    ):
        stmt = select(VkMessage).distinct(VkMessage.conversation_id)

        try:
            async with self.app.database.session() as session:
                messages = await session.scalars(stmt)
        except Exception as exc:
            self.logger.exception(exc_info=exc, msg=exc)
            raise HTTPServiceUnavailable from exc

        vk_messages = messages.unique().all()

        if len(vk_messages) == 0:
            raise HTTPNotFound

        return vk_messages
