from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.game.constants import GameStage
from app.quiz.models import Answer, Question
from app.store.database.sqlalchemy_base import BaseModel


class GameSettings(BaseModel):
    __tablename__ = "game_settings"
    __table_args__ = (
        UniqueConstraint(
            "time_to_registration",
            "min_count_gamers",
            "max_count_gamers",
            "time_to_answer",
            name="profile_name",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_name: Mapped[str] = mapped_column(
        String[20], nullable=False, unique=True
    )
    time_to_registration: Mapped[int] = mapped_column(default=15)
    min_count_gamers: Mapped[int] = mapped_column(default=1)
    max_count_gamers: Mapped[int] = mapped_column(default=6)
    time_to_answer: Mapped[int] = mapped_column(default=15)
    description: Mapped[str | None] = mapped_column(String(1000))

    games: Mapped[list["Game"]] = relationship(back_populates="profile")

    def __str__(self):
        if self.description:
            return (
                f"Профиль № {self.id} - {self.profile_name}\n"
                f"#### {self.description}\n#####\n"
                f" Время на регистрацию: {self.time_to_registration} секунд\n"
                f" Время на ответ: {self.time_to_answer} секунд "
            )
        return f"Профиль № {self.id} - {self.profile_name}"

    def __repr__(self):
        return str(self)


class Game(BaseModel):
    __tablename__ = "games"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int | None] = mapped_column(default=None)
    admin_game_id: Mapped[int | None] = mapped_column(default=None)
    pinned_conversation_message_id: Mapped[int | None] = mapped_column(
        default=None
    )
    responsed_player_id: Mapped[int | None] = mapped_column(
        server_default=None, default=None
    )
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    state: Mapped[PG_ENUM] = mapped_column(PG_ENUM(GameStage), nullable=False)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("game_settings.id"), default=1
    )

    profile: Mapped["GameSettings"] = relationship(back_populates="games")
    question: Mapped["Question"] = relationship(back_populates="games")
    players: Mapped[list["Player"]] = relationship(back_populates="game")
    player_answers_games: Mapped[list["PlayerAnswerGame"]] = relationship(
        back_populates="game", cascade="all, delete-orphan"
    )


class Player(BaseModel):
    __tablename__ = "players"
    __table_args__ = (
        UniqueConstraint("vk_user_id", "game_id", name="vk_user_id_game_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vk_user_id: Mapped[int] = mapped_column(nullable=False, primary_key=True)
    name: Mapped[str] = mapped_column(String[50])
    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.id"), primary_key=True
    )

    game: Mapped["Game"] = relationship(back_populates="players")
    player_answers_games: Mapped[list["PlayerAnswerGame"]] = relationship(
        back_populates="player", cascade="all, delete-orphan"
    )


class PlayerAnswerGame(BaseModel):
    __tablename__ = "player_answers_games"
    __table_args__ = (
        UniqueConstraint(
            "player_id",
            "game_id",
            "answer_id",
            name="idx_unique_player_game_answer",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id"), nullable=False
    )
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)
    answer_id: Mapped[int] = mapped_column(
        ForeignKey("answers.id"), nullable=False
    )

    player: Mapped[list["Player"]] = relationship(
        back_populates="player_answers_games"
    )
    game: Mapped["Game"] = relationship(back_populates="player_answers_games")
    answer: Mapped["Answer"] = relationship(
        back_populates="player_answers_games"
    )
