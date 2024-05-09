from enum import Enum

from sqlalchemy import Enum as PGEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.quize.models import Answer, Question
from app.store.database import BaseModel


class GameStage(Enum):
    NOT_START = "NOT_START"
    REGISTRATION_GAMERS = "REGISTRATION_GAMERS"
    WAITING_CALLBACK = "WAITING_CALLBACK"
    WAITING_ANSWER = "WAITING_ANSWER"
    FINISHED = "FINISHED"
    CANCELED = "CANCELED"


class Game(BaseModel):
    __tablename__ = "games"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int | None] = mapped_column(default=None)
    pinned_conversation_message_id: Mapped[int | None] = mapped_column(
        default=None
    )
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    game_stage: Mapped[PGEnum] = mapped_column(
        PGEnum(GameStage), default=GameStage.NOT_START
    )

    question: Mapped["Question"] = relationship(back_populates="games")
    players: Mapped[list["Player"]] = relationship(back_populates="game")
    player_answers_games: Mapped[list["PlayerAnswerGame"]] = relationship(
        back_populates="game", cascade="all, delete-orphan"
    )


class Player(BaseModel):
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(primary_key=True)
    vk_user_id: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String[50])
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))

    game: Mapped["Game"] = relationship(back_populates="players")
    player_answers_games: Mapped[list["PlayerAnswerGame"]] = relationship(
        back_populates="player", cascade="all, delete-orphan"
    )


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
