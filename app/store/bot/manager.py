import typing
from logging import getLogger

from app.store.vk_api.dataclasses import Message, VkUpdate

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")

    async def handle_updates(self, updates: list[VkUpdate]):
        for update in updates:
            await self.app.store.vk_api.send_personal_message(
                Message(
                    peer_id=update.vk_object.peer_id,
                    text=update.vk_object.text,
                )
            )
