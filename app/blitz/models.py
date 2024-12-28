from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.games.blitz.models import BlitzGame, BlitzQuestionGame
from app.store.database.sqlalchemy_base import BaseModel


class GameBlitzTheme(BaseModel):
    __tablename__ = "blitz_themes"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String[50], unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String[500], default=None)

    questions: Mapped[list["GameBlitzQuestion"]] = relationship(
        back_populates="theme", cascade="all, delete-orphan"
    )


class GameBlitzQuestion(BaseModel):
    __tablename__ = "blitz_questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String[500], index=True)
    answer: Mapped[str] = mapped_column(String[100])
    theme_id: Mapped[int] = mapped_column(ForeignKey("blitz_themes.id"))

    theme: Mapped["GameBlitzTheme"] = relationship(back_populates="questions")
    blitz_question_game: Mapped[list["BlitzQuestionGame"]] = relationship(
        back_populates="blitz_question", cascade="all, delete-orphan"
    )
    # game: Mapped["BlitzGame"] = relationship(back_populates="questions")

    # blitz_question_game: Mapped[list["BlitzQuestionGame"]] = relationship(
    #     back_populates="question", cascade="all, delete-orphan"
    # )
    # blitz_player_question_game: Mapped[list["BlitzPlayerQuestionGame"]] = relationship(
    #     back_populates="question", cascade="all, delete-orphan"
    # )
