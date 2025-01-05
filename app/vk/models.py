from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.store.database import BaseModel


class VkMessage(BaseModel):
    __tablename__ = "vk_messages"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(nullable=False)
    text: Mapped[str] = mapped_column(nullable=False)
    user_id: Mapped[int] = mapped_column(nullable=False)
    date: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
