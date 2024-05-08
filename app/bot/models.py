from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.quize.models import QuestionModel
from app.store.database import BaseModel


class GameModel(BaseModel):
    __tablename__ = "games"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int | None] = mapped_column(default=None)
    pinned_conversation_message_id: Mapped[int | None] = mapped_column(
        default=None
    )

    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    question: Mapped["QuestionModel"] = relationship(back_populates="answers")

    stage_id: Mapped[int] = mapped_column(ForeignKey("stages.id"))
    stages: Mapped["StageModel"] = relationship(back_populates="stages")


class StageModel(BaseModel):
    __tablename__ = "stages"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(String[40])

    games: Mapped[list["GameModel"]] = relationship(
        relationship(back_populates="games")
    )
