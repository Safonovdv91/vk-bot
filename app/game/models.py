from enum import Enum

from sqlalchemy import ForeignKey, String, UniqueConstraint, select
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.quiz.models import Answer, Question
from app.store.database.sqlalchemy_base import BaseModel


class GameStage(Enum):
    WAIT_INIT = "WAIT_INIT"
    REGISTRATION_GAMERS = "REGISTRATION_GAMERS"
    WAITING_READY_TO_ANSWER = "WAITING_CALLBACK"
    WAITING_ANSWER = "WAITING_ANSWER"
    FINISHED = "FINISHED"
    CANCELED = "CANCELED"


class Game(BaseModel):
    __tablename__ = "games"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int | None] = mapped_column(
        default=None
    )
    pinned_conversation_message_id: Mapped[int | None] = mapped_column(
        default=None
    )
    responsed_player_id: Mapped[int | None] = mapped_column(
        server_default=None, default=None
    )
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    state: Mapped[PG_ENUM] = mapped_column(PG_ENUM(GameStage), nullable=False)

    question: Mapped["Question"] = relationship(back_populates="games")
    players: Mapped[list["Player"]] = relationship(back_populates="game")
    player_answers_games: Mapped[list["PlayerAnswerGame"]] = relationship(
        back_populates="game", cascade="all, delete-orphan"
    )


class Player(BaseModel):
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(primary_key=True)
    vk_user_id: Mapped[int] = mapped_column(nullable=False, primary_key=True)
    name: Mapped[str] = mapped_column(String[50])
    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.id"), primary_key=True
    )

    game: Mapped["Game"] = relationship(back_populates="players")
    player_answers_games: Mapped[list["PlayerAnswerGame"]] = relationship(
        back_populates="player", cascade="all, delete-orphan"
    )
    __table_args__ = (
        UniqueConstraint("vk_user_id", "game_id", name="vk_user_id_game_id"),
    )

    async def get_games(self, session):
        stmt = select(Game).where(self.game_id == Game.id)
        result = await session.execute(stmt)
        return result.scalars().all()


class PlayerAnswerGame(BaseModel):
    __tablename__ = "player_answers_games"
    id: Mapped[int] = mapped_column(primary_key=True)

    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))
    answer_id: Mapped[int] = mapped_column(ForeignKey("answers.id"))

    player: Mapped[list["Player"]] = relationship(
        back_populates="player_answers_games"
    )
    game: Mapped["Game"] = relationship(back_populates="player_answers_games")
    answer: Mapped["Answer"] = relationship(
        back_populates="player_answers_games"
    )
