from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.quize.models import AnswerModel, QuestionModel
from app.store.database import BaseModel


class GameModel(BaseModel):
    __tablename__ = "games"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int | None] = mapped_column(default=None)
    pinned_conversation_message_id: Mapped[int | None] = mapped_column(
        default=None
    )
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    stage_id: Mapped[int] = mapped_column(ForeignKey("stages.id"))

    stage: Mapped["StageModel"] = relationship(back_populates="games")
    question: Mapped["QuestionModel"] = relationship(back_populates="games")
    players: Mapped[list["PlayerModel"]] = relationship(
        back_populates="game"
    )
    player_answers_games: Mapped[list["PlayerAnswerGameModel"]] = relationship(
        back_populates="game", cascade="all, delete-orphan"
    )


class StageModel(BaseModel):
    __tablename__ = "stages"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(String[40])

    games: Mapped[list["GameModel"]] = relationship(back_populates="stage")


class PlayerModel(BaseModel):
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(primary_key=True)
    vk_user_id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(String[50])
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))

    game: Mapped["GameModel"] = relationship(back_populates="players")
    player_answers_games: Mapped[list["PlayerAnswerGameModel"]] = relationship(
        back_populates="player", cascade="all, delete-orphan"
    )


class PlayerAnswerGameModel(BaseModel):
    __tablename__ = "player_answers_games"
    id: Mapped[int] = mapped_column(primary_key=True)

    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))
    answer_id: Mapped[int] = mapped_column(ForeignKey("answers.id"))

    player: Mapped["PlayerModel"] = relationship(
        back_populates="player_answers_games"
    )
    game: Mapped["GameModel"] = relationship(
        back_populates="player_answers_games"
    )
    answer: Mapped["AnswerModel"] = relationship(
        back_populates="player_answers_games"
    )
