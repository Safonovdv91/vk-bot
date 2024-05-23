import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.game.constants import GameStage
from app.game.models import Game, GameSettings
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
async def game_settings(
    db_sessionmaker,
) -> GameSettings:
    game_settings = GameSettings(
        profile_name="test",
        time_to_registration=30,
        min_count_gamers=2,
        max_count_gamers=6,
        time_to_answer=15,
    )
    async with db_sessionmaker() as session:
        session.add(game_settings)
        await session.commit()

    return game_settings


@pytest.fixture
async def game1(
    db_sessionmaker,
    theme_1: Theme,
    question_1: Question,
    game_settings: GameSettings,
) -> Game:
    game = Game(
        conversation_id=2000002,
        admin_game_id=123411234,
        pinned_conversation_message_id=22,
        responsed_player_id=None,
        question_id=question_1.id,
        state=GameStage.WAITING_READY_TO_ANSWER,
        profile_id=game_settings.id,
    )
    async with db_sessionmaker() as session:
        session.add(game)
        await session.commit()

    return game


@pytest.fixture
async def game_finished(
    db_sessionmaker,
    theme_1: Theme,
    question_1: Question,
    game_settings: GameSettings,
) -> Game:
    game = Game(
        conversation_id=2000003,
        admin_game_id=123412234,
        pinned_conversation_message_id=20,
        responsed_player_id=None,
        question_id=question_1.id,
        state=GameStage.FINISHED,
        profile_id=game_settings.id,
    )
    async with db_sessionmaker() as session:
        session.add(game)
        await session.commit()

    return game


@pytest.fixture
async def game_canceled(
    db_sessionmaker,
    theme_1: Theme,
    question_1: Question,
    game_settings: GameSettings,
) -> Game:
    game = Game(
        conversation_id=2000003,
        admin_game_id=123412234,
        pinned_conversation_message_id=20,
        responsed_player_id=None,
        question_id=question_1.id,
        state=GameStage.CANCELED,
        profile_id=game_settings.id,
    )
    async with db_sessionmaker() as session:
        session.add(game)
        await session.commit()

    return game


@pytest.fixture
async def game_running(
    db_sessionmaker,
    theme_1: Theme,
    question_1: Question,
    game_settings: GameSettings,
) -> Game:
    game = Game(
        conversation_id=2000003,
        admin_game_id=123412234,
        pinned_conversation_message_id=20,
        responsed_player_id=None,
        question_id=question_1.id,
        state=GameStage.WAITING_ANSWER,
        profile_id=game_settings.id,
    )

    async with db_sessionmaker() as session:
        session.add(game)
        await session.commit()

    return game
