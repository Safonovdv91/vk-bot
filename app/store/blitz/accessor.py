from collections.abc import Sequence
from typing import TYPE_CHECKING

import sqlalchemy.exc
from aiohttp.web_exceptions import (
    HTTPBadRequest,
    HTTPConflict,
    HTTPNotFound,
    HTTPServiceUnavailable,
)
from sqlalchemy import delete, update
from sqlalchemy.future import select

from app.base.base_accessor import BaseAccessor
from app.blitz.models import GameBlitzQuestion, GameBlitzTheme

if TYPE_CHECKING:
    from app.web.app import Application


class BlitzAccessor(BaseAccessor):
    async def connect(self, app: "Application") -> None:
        self.logger.info("Подключаем BlitzAccessor")

        # if await self.get_theme_by_id(1) is None:
        #     self.logger.info("Создаем базовую тему.")
        #     await self.create_theme(
        #         title="default", description="default theme"
        #     )

        # if await self.get_question_by_id(1) is None:
        #     self.logger.info("Создаем базовые вопросы")
        #     for question in default_questions:
        #         await self.create_question(
        #             title=question.title,
        #             theme_id=question.theme_id,
        #             answers=question.answers,
        #         )

    async def create_theme(
        self, title: str, description: str | None = None
    ) -> GameBlitzTheme:
        async with self.app.database.session() as session:
            theme = GameBlitzTheme(title=title, description=description)
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

    async def get_theme_by_title(self, title: str) -> GameBlitzTheme | None:
        async with self.app.database.session() as session:
            title = await session.execute(
                select(GameBlitzTheme).where(GameBlitzTheme.title == title)
            )

        return title.scalar_one_or_none()

    async def get_theme_by_id(self, id_: int) -> GameBlitzTheme | None:
        async with self.app.database.session() as session:
            theme = await session.execute(
                select(GameBlitzTheme).where(GameBlitzTheme.id == int(id_))
            )

        return theme.scalar_one_or_none()

    async def get_themes_list(
        self, limit: int | None = None, offset: int | None = None
    ) -> Sequence[GameBlitzTheme]:
        async with self.app.database.session() as session:
            stmt = select(GameBlitzTheme)

            if limit is not None:
                stmt = stmt.limit(limit)
            if offset is not None:
                stmt = stmt.offset(offset)

            result = await session.execute(stmt)

        return result.scalars().all()

    async def delete_theme_by_id(self, id_: int) -> GameBlitzTheme | None:
        async with self.app.database.session() as session:
            theme = await session.get(GameBlitzTheme, id_)

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
        self, title: str, theme_id: int, answer: str
    ) -> GameBlitzQuestion:
        async with self.app.database.session() as session:
            question = GameBlitzQuestion(title=title, theme_id=theme_id, answer=answer)

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

    async def get_question_by_id(self, id_: int) -> GameBlitzQuestion | None:
        async with self.app.database.session() as session:
            result = await session.execute(
                select(GameBlitzQuestion).where(GameBlitzQuestion.id == id_)
            )

        return result.unique().scalar_one_or_none()

    async def get_question_by_title(self, title: str) -> GameBlitzQuestion | None:
        stmt = select(GameBlitzQuestion).where(GameBlitzQuestion.title == title)

        async with self.app.database.session() as session:
            return await session.scalar(stmt)

    async def get_questions_list(
        self,
        theme_id: int | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> Sequence[GameBlitzQuestion]:
        if theme_id is None:
            raise HTTPBadRequest

        stmt = select(GameBlitzQuestion).where(
            GameBlitzQuestion.theme_id == int(theme_id)
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

    async def delete_question_by_id(self, id_: int) -> GameBlitzQuestion | None:
        async with self.app.database.session() as session:
            try:
                question = (
                    await session.execute(
                        select(GameBlitzQuestion).where(GameBlitzQuestion.id == id_)
                    )
                ).unique()
                question = question.scalar_one_or_none()

                if question is None:
                    raise HTTPBadRequest(
                        reason="Вопроса с таки id не существует," " или он был уже удален"
                    )

                stmt = delete(GameBlitzQuestion).where(GameBlitzQuestion.id == id_)
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

    async def update_question(
        self,
        question_id: int,
        new_title: str | None,
        new_theme_id: int | None,
        new_answer: str | None,
    ):
        async with self.app.database.session() as session:
            try:
                stmt = select(GameBlitzQuestion).where(
                    GameBlitzQuestion.id == question_id
                )
                result = await session.execute(stmt)
                question = result.scalar_one_or_none()

                if not question:
                    raise HTTPBadRequest(reason="Вопрос не найден")

                stmt = update(GameBlitzQuestion).where(
                    GameBlitzQuestion.id == question_id
                )
                if new_title:
                    stmt = stmt.values(title=new_title)
                if new_theme_id:
                    stmt = stmt.values(theme_id=new_theme_id)
                if new_answer:
                    stmt = stmt.values(answer=new_answer)

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
