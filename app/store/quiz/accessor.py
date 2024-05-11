from collections.abc import Iterable, Sequence

from aiohttp.web_exceptions import HTTPForbidden
from sqlalchemy import select
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
            theme = await self.get_theme_by_title(title)
            if theme:
                raise HTTPForbidden
            theme = Theme(title=title, description=description)
            self.logger.info("Добавляем в базу данных %s", theme)
            session.add(theme)
            await session.commit()
            return theme

    async def get_theme_by_title(self, title: str) -> Theme | None:
        async with self.app.database.session() as session:
            query = select(Theme).where(Theme.title == title)
        return await session.scalar(query)

    async def get_theme_by_id(self, id_: int) -> Theme | None:
        async with self.app.database.session() as session:
            theme = await session.execute(
                select(Theme).where(Theme.id == int(id_))
            )
        return theme.scalar_one_or_none()

    async def list_themes(self) -> Sequence[Theme]:
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
            session.add(question)
            await session.commit()
        return question

    async def get_question_by_id(self, id_: int) -> Question | None:
        id_ = int(id_)
        stmt = (
            select(Question)
            .where(Question.id == id_)
            .options(joinedload(Question.answers))
        )
        async with self.app.database.session() as session:
            return await session.scalar(stmt)

    async def get_question_by_title(self, title: str) -> Question | None:
        stmt = (
            select(Question)
            .where(Question.title == title)
            .options(joinedload(Question.answers))
        )
        async with self.app.database.session() as session:
            return await session.scalar(stmt)

    async def list_questions(
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
        question: Question = await self.get_question_by_id(id_)
        if question is None:
            return None
        async with self.app.database.session() as session:
            await session.delete(question)
            await session.commit()
        return question
