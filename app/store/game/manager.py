import typing
from logging import getLogger

from app.store.vk_api.dataclasses import (
    Update,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("BotManager")

    async def handle_events(self, events: list[Update]):
        """Обработка callback событий"""
        self.logger.info("Получены события \n %s", events)

        for event in events:
            self.logger.info(
                "Пришло нажатие кнопки с %s", event.object.payload.text
            )

    async def handle_updates(self, updates: list[Update]):
        """Обработка пришедших сообщений"""
        self.logger.info("Получены события \n %s", updates)

        for update in updates:
            self.logger.info("Пришло сообщение %s", update.object.message.text)
