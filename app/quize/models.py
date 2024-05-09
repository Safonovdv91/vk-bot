import typing

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.store.database.sqlalchemy_base import BaseModel

if typing.TYPE_CHECKING:
    from app.bot.models import GameModel, PlayerAnswerGameModel


class ThemeModel(BaseModel):
    __tablename__ = "themes"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String[30], unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String[300], default=None)

    questions: Mapped[list["QuestionModel"]] = relationship(
        back_populates="theme", cascade="all, delete-orphan"
    )


class QuestionModel(BaseModel):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String[300], unique=True, index=True)

    theme_id: Mapped[int] = mapped_column(ForeignKey("themes.id"))
    theme: Mapped["ThemeModel"] = relationship(back_populates="questions")

    answers: Mapped[list["AnswerModel"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )

    games: Mapped[list["GameModel"]] = relationship(back_populates="question")


class AnswerModel(BaseModel):
    __tablename__ = "answers"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String[50], unique=True)
    score: Mapped[int] = mapped_column(default=1, nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))

    question: Mapped["QuestionModel"] = relationship(back_populates="answers")
    player_answers_games: Mapped[list["PlayerAnswerGameModel"]] = relationship(
        back_populates="answer", cascade="all, delete-orphan"
    )
