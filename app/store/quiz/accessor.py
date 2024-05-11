from collections.abc import Iterable, Sequence

import sqlalchemy.exc
from aiohttp.web_exceptions import (
    HTTPBadRequest,
    HTTPConflict,
    HTTPServiceUnavailable,
)
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.base.base_accessor import BaseAccessor
from app.quiz.models import (
    Answer,
    Question,
    Theme,
)


class QuizAccessor(BaseAccessor):
    async def create_theme(
        self, title: str, description: str | None = None
    ) -> Theme:
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
            title = await session.execute(
                select(Theme).where(Theme.title == title)
            )

        return title.scalar_one_or_none()

    async def get_theme_by_id(self, id_: int) -> Theme | None:
        async with self.app.database.session() as session:
            theme = await session.execute(
                select(Theme).where(Theme.id == int(id_))
            )

        return theme.scalar_one_or_none()

    async def get_themes_list(self) -> Sequence[Theme]:
        async with self.app.database.session() as session:
            result = await session.execute(select(Theme))

        return result.scalars().all()

    async def delete_theme_by_id(self, id_: int) -> Theme | None:
        async with self.app.database.session() as session:
            theme = await self.get_theme_by_id(id_)

            if theme is None:
                return None

            await session.delete(theme)
            await session.commit()

        return theme

    async def create_question(
        self, title: str, theme_id: int, answers: Iterable[Answer]
    ) -> Question:
        async with self.app.database.session() as session:
            question = Question(title=title, theme_id=theme_id, answers=answers)

            try:
                session.add(question)
                await session.commit()

            except sqlalchemy.exc.IntegrityError as exc:
                self.logger.exception(exc_info=exc, msg=exc)
                raise HTTPBadRequest(
                    reason="не удалось добавить вопрос"
                ) from exc

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
            question = result.unique().scalar_one_or_none()

        return question

    async def get_question_by_title(self, title: str) -> Question | None:
        stmt = (
            select(Question)
            .where(Question.title == title)
            .options(joinedload(Question.answers))
        )

        async with self.app.database.session() as session:
            return await session.scalar(stmt)

    async def get_questions_list(
        self, theme_id: int | None = None
    ) -> Sequence[Question]:
        stmt = select(Question)

        if theme_id:
            stmt = stmt.where(Question.theme_id == int(theme_id))

        stmt = stmt.options(joinedload(Question.answers))

        async with self.app.database.session() as session:
            questions = await session.scalars(stmt)

        return questions.unique().all()

    async def delete_question_by_id(self, id_: int) -> Question | None:
        async with self.app.database.session() as session:
            try:
                async with session.begin():
                    question = (
                        await session.execute(
                            select(Question).where(Question.id == id_)
                        )
                    ).scalar_one_or_none()

                    if question is None:
                        raise HTTPBadRequest

                    await session.delete(question)

            except sqlalchemy.exc.IntegrityError as exc:
                await session.rollback()
                self.logger.exception(exc_info=exc, msg=exc)
                raise HTTPConflict(reason="Не удалось удалить вопрос") from exc

            except sqlalchemy.exc.InterfaceError as exc:
                await session.rollback()
                self.logger.exception(exc_info=exc, msg=exc)
                raise HTTPServiceUnavailable from exc

            else:
                return question
