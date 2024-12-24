from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

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

    theme_id: Mapped[int] = mapped_column(ForeignKey("blitz_themes.id"))
    theme: Mapped["GameBlitzTheme"] = relationship(back_populates="questions")
    answer: Mapped[str] = mapped_column(String[100])
