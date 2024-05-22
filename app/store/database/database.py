from logging import getLogger
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.store.database.sqlalchemy_base import BaseModel

if TYPE_CHECKING:
    from app.web.app import Application


class Database:
    def __init__(self, app: "Application") -> None:
        self.app = app
        self.logger = getLogger("database")

        self.engine: AsyncEngine | None = None
        self._db: type[DeclarativeBase] = BaseModel
        self.session: async_sessionmaker[AsyncSession] | None = None

    async def connect(self, *args: Any, **kwargs: Any) -> None:
        host: str = self.app.config.database.host
        port: int = self.app.config.database.port
        user: str = self.app.config.database.user
        password: str = self.app.config.database.password
        database: str = self.app.config.database.database

        self.engine = create_async_engine(
            url=f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}",
            echo=False,
            future=True,
        )

        self.session = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def disconnect(self, *args: Any, **kwargs: Any) -> None:
        try:
            self.logger.info("Отключаем БД")
            await self.engine.dispose()
        except Exception:
            self.logger.exception("Что-то не отключилось")
