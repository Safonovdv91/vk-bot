from hashlib import sha256
from typing import Self

from aiohttp_session import Session
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.store.database.sqlalchemy_base import BaseModel


class AdminModel(BaseModel):
    __tablename__ = "admins"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String[30], unique=True, index=True)
    password: Mapped[str | None] = mapped_column(String(128))

    @classmethod
    def from_session(cls, session: Session) -> Self:
        return AdminModel(
            email=session["admin"]["email"], password=session["admin"]["email"]
        )

    def is_password_valid(self, password: str) -> bool:
        password_hash = sha256(password.encode()).hexdigest()
        return password_hash == self.password
