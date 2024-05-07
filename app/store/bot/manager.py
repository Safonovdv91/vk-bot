import typing
from logging import getLogger

from app.store.vk_api.dataclasses import SendMessage, Update

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")

    async def handle_updates(self, updates: list[Update]):
        for update in updates:
            await self.app.store.vk_api.send_personal_message(
                SendMessage(
                    peer_id=update.object.message.peer_id,
                    text=update.object.message.text,
                )
            )
