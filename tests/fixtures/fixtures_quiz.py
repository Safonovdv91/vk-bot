import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.game.models import Game
from app.quiz.models import (
    Answer,
    Question,
    Theme,
)


@pytest.fixture
async def theme_1(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> Theme:
    new_theme = Theme(title="default_test")

    async with db_sessionmaker() as session:
        session.add(new_theme)
        await session.commit()

    return new_theme


@pytest.fixture
async def theme_2(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> Theme:
    new_theme = Theme(title="theme2_test")

    async with db_sessionmaker() as session:
        session.add(new_theme)
        await session.commit()

    return new_theme


@pytest.fixture
async def question_1(
    db_sessionmaker: async_sessionmaker[AsyncSession], theme_1: Theme
) -> Question:
    answers = [
        Answer(title="Еду", score=43),
        Answer(title="свадьбу", score=27),
        Answer(title="природу", score=15),
        Answer(title="животных", score=15),
    ]

    question = Question(
        title="Кого или что чаще всего снимает фотограф?",
        theme_id=1,
        answers=answers,
    )

    async with db_sessionmaker() as session:
        session.add(question)
        await session.commit()

    return question


@pytest.fixture
async def question_2(db_sessionmaker, theme_1: Theme) -> Question:
    answers = [
        Answer(title="Москва", score=34),
        Answer(title="санкт-петербург", score=17),
        Answer(title="новосибирск", score=14),
        Answer(title="казань", score=12),
        Answer(title="екатеринбург", score=8),
        Answer(title="Самара", score=5),
    ]

    question = Question(
        title="В каком городе России есть метро?",
        theme_id=1,
        answers=answers,
    )

    async with db_sessionmaker() as session:
        session.add(question)
        await session.commit()

    return question


@pytest.fixture
async def game1(db_sessionmaker, theme_1: Theme, question_1) -> Question:
    game = Game()
    async with db_sessionmaker() as session:
        session.add(game)
        await session.commit()

    return game
