import typing

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.games.blitz.constants import BlitzGameStage
from app.store.database.sqlalchemy_base import BaseModel

if typing.TYPE_CHECKING:
    from app.blitz.models import GameBlitzQuestion, GameBlitzTheme


class GameBlitzSettings(BaseModel):
    __tablename__ = "blitz_game_settings"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_name: Mapped[str] = mapped_column(String[50], nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(1000))

    games: Mapped[list["BlitzGame"]] = relationship(back_populates="profile")

    def __str__(self):
        if self.description:
            return (
                f"Профиль № {self.id} - {self.profile_name}\n"
                f"#### {self.description}\n#####\n"
            )
        return f"Профиль № {self.id} - {self.profile_name}"

    def __repr__(self):
        return str(self)


class BlitzGame(BaseModel):
    __tablename__ = "blitz_games"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int | None] = mapped_column(default=None)
    pinned_conversation_message_id: Mapped[int | None] = mapped_column(default=None)
    game_stage: Mapped[PG_ENUM] = mapped_column(PG_ENUM(BlitzGameStage), nullable=False)
    admin_game_id: Mapped[int | None] = mapped_column(default=None)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("blitz_game_settings.id"), default=1
    )
    theme_id: Mapped[int] = mapped_column(
        ForeignKey("blitz_themes.id"), default=1
    )

    theme: Mapped["GameBlitzTheme"] = relationship(back_populates="games")
    profile: Mapped["GameBlitzSettings"] = relationship(back_populates="games")

    blitz_question_game: Mapped[list["BlitzQuestionGame"]] = relationship(
        back_populates="blitz_game", cascade="all, delete-orphan"
    )
    blitz_player_question_game: Mapped[list["BlitzPlayerQuestionGame"]] = relationship(
        back_populates="blitz_game", cascade="all, delete-orphan"
    )

    def __str__(self):
        return (
            f"Игра № {self.id} - проведенная в беседе {self.conversation_id}"
            f"находится в режиме {self.game_stage.name}"
        )

    def __repr__(self):
        return str(self)


class GameBlitzPlayer(BaseModel):
    "Таблица игроков в игре блитц"

    __tablename__ = "blitz_players"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vk_user_id: Mapped[int] = mapped_column(nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String[50])

    blitz_player_question_game: Mapped[list["BlitzPlayerQuestionGame"]] = relationship(
        back_populates="blitz_player", cascade="all, delete-orphan"
    )


class BlitzQuestionGame(BaseModel):
    __tablename__ = "blitz_question_games"
    __table_args__ = (
        UniqueConstraint(
            "question_id",
            "game_id",
            name="idx_unique_blitz_question_game",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)

    question_id: Mapped[int] = mapped_column(
        ForeignKey("blitz_questions.id"), nullable=False
    )
    game_id: Mapped[int] = mapped_column(ForeignKey("blitz_games.id"), nullable=False)

    blitz_game: Mapped["BlitzGame"] = relationship(back_populates="blitz_question_game")
    blitz_question: Mapped["GameBlitzQuestion"] = relationship(
        back_populates="blitz_question_game"
    )


class BlitzPlayerQuestionGame(BaseModel):
    """Сводная таблица где отмечено какой игрок в какой игре ответил на вопрос
    player_id - идентификатор игрока
    game_id - идентификатор игры
    question_id - идентификатор вопроса
    """

    __tablename__ = "blitz_player_question_games"
    __table_args__ = (
        UniqueConstraint(
            "player_id",
            "game_id",
            "question_id",
            name="idx_unique_blitz_player_game_question",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)

    player_id: Mapped[int] = mapped_column(ForeignKey("blitz_players.id"), nullable=False)
    game_id: Mapped[int] = mapped_column(ForeignKey("blitz_games.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("blitz_questions.id"), nullable=False
    )

    blitz_player: Mapped["GameBlitzPlayer"] = relationship(
        back_populates="blitz_player_question_game"
    )
    blitz_question: Mapped["GameBlitzQuestion"] = relationship(
        back_populates="blitz_player_question_game"
    )
    blitz_game: Mapped["BlitzGame"] = relationship(
        back_populates="blitz_player_question_game"
    )
