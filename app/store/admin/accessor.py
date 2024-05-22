from hashlib import sha256
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.admin.models import AdminModel
from app.base.base_accessor import BaseAccessor

if TYPE_CHECKING:
    from app.web.app import Application


class AdminAccessor(BaseAccessor):
    async def connect(self, app: "Application") -> None:
        self.logger.info("Инициализируем начального юзера")
        await self.upsert_admin(
            email=app.config.admin.email, password=app.config.admin.password
        )

    async def get_by_email(self, email: str) -> AdminModel | None:
        async with self.app.database.session() as session:
            query = select(AdminModel).where(AdminModel.email == email)
            return await session.scalar(query)

    async def upsert_admin(self, email: str, password: str) -> AdminModel:
        admin_data = {
            "email": email,
            "password": sha256(password.encode()).hexdigest(),
        }

        stmt = insert(AdminModel).values(admin_data)
        stmt = stmt.on_conflict_do_nothing(index_elements=["email"])

        async with self.app.database.session() as session:
            await session.execute(stmt)
            await session.commit()

            return await self.get_by_email(email)
