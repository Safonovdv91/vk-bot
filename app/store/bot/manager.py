import json
import typing
from logging import getLogger

from app.store.vk_api.utils import VkKeyboard, VkButton
from app.store.vk_api.dataclasses import (
    SendMessage,
    SendMessageWithKeyboard,
    Update,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")

    async def handle_updates(self, updates: list[Update]):

        vk_keyboard_start_game = VkKeyboard(one_time=False, inline=False)
        btn1 = VkButton(label="Стоп игра", color="primary")
        btn21 = VkButton(label="СТОП ИГРА", color="secondary")
        btn22 = VkButton(label="СТОООП", color="secondary")
        vk_keyboard_start_game.add_line(
            [btn1.get()]
        )
        # Две маленькие кнопки в одном ряду
        vk_keyboard_start_game.add_line(
            [btn21.get(), btn22.get()]
        )
        vk_keyboard_stop_game = VkKeyboard(one_time=True, inline=False)

        for update in updates:
            if update.object.message.text.lower() == "старт игры":

                await self.app.store.vk_api.send_message_with_keyboard(
                    SendMessageWithKeyboard(
                        peer_id=update.object.message.peer_id,
                        text=update.object.message.text,
                        keyboard=vk_keyboard_start_game.get_keyboard(),
                    ),
                )

            if update.object.message.text.lower() == "стоооп":
                await self.app.store.vk_api.send_message_with_keyboard(
                    SendMessageWithKeyboard(
                        peer_id=update.object.message.peer_id,
                        text=f"НУ И ПОШЕЛ В ЗАДНИЦУ",
                        keyboard=vk_keyboard_stop_game.get_keyboard(),
                    ),
                )