import typing

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.store.database.sqlalchemy_base import BaseModel

if typing.TYPE_CHECKING:
    from app.game.models import Game, PlayerAnswerGame


class Theme(BaseModel):
    __tablename__ = "themes"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String[30], unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String[300], default=None)

    questions: Mapped[list["Question"]] = relationship(
        back_populates="theme", cascade="all, delete-orphan"
    )


class Question(BaseModel):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String[300], index=True)

    theme_id: Mapped[int] = mapped_column(ForeignKey("themes.id"))
    theme: Mapped["Theme"] = relationship(back_populates="questions")

    answers: Mapped[list["Answer"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )

    games: Mapped[list["Game"]] = relationship(back_populates="question")


class Answer(BaseModel):
    __tablename__ = "answers"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String[50])
    score: Mapped[int] = mapped_column(default=1, nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))

    question: Mapped["Question"] = relationship(back_populates="answers")
    player_answers_games: Mapped[list["PlayerAnswerGame"]] = relationship(
        back_populates="answer", cascade="all, delete-orphan"
    )
