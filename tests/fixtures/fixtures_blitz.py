import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.blitz.models import GameBlitzQuestion, GameBlitzTheme
from app.games.blitz.logic import GameBlitz


@pytest.fixture
async def blitz_theme_1(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> GameBlitzTheme:
    new_theme = GameBlitzTheme(
        title="default test blitz theme", description="test blitz theme description"
    )

    async with db_sessionmaker() as session:
        session.add(new_theme)
        await session.commit()

    return new_theme


@pytest.fixture
async def blitz_theme_2(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> GameBlitzTheme:
    new_theme = GameBlitzTheme(
        title="default test blitz theme 2",
    )

    async with db_sessionmaker() as session:
        session.add(new_theme)
        await session.commit()

    return new_theme


@pytest.fixture
async def blitz_question_1(
    db_sessionmaker: async_sessionmaker[AsyncSession],
    blitz_theme_1: GameBlitzTheme,
) -> GameBlitzQuestion:
    new_question = GameBlitzQuestion(
        title="Default Question 1", theme_id=blitz_theme_1.id, answer="answer 1"
    )

    async with db_sessionmaker() as session:
        session.add(new_question)
        await session.commit()

    return new_question


@pytest.fixture
async def blitz_question_2(
    db_sessionmaker: async_sessionmaker[AsyncSession],
    blitz_theme_1: GameBlitzTheme,
) -> GameBlitzQuestion:
    new_question = GameBlitzQuestion(
        title="Default Question 2", theme_id=blitz_theme_1.id, answer="answer 2"
    )

    async with db_sessionmaker() as session:
        session.add(new_question)
        await session.commit()

    return new_question


@pytest.fixture
def mock_questions():
    """Создает фиктивные вопросы для игры"""
    return [
        GameBlitzQuestion(title="Вопрос 1", answer="Ответ 1"),
        GameBlitzQuestion(title="Вопрос 2", answer="Ответ 2"),
    ]


@pytest.fixture
def game_blitz(mock_app, mock_questions):
    return GameBlitz(app=mock_app, questions=mock_questions)
