import typing
from logging import getLogger

from app.store.vk_api.dataclasses import (
    SendMessage,
    SendMessageWithKeyboard,
    Update,
)
from app.store.vk_api.utils import VkButton, VkKeyboard

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("BotManager")
        self.game_on = False

    async def handle_events(self, events: list[Update]):
        self.logger.info("Получены события \n %s", events)
        for event in events:
            await self.app.store.vk_api.send_event_answer(
                event_id=event.object.event_id,
                user_id=event.object.user_id,
                response_text="Нажата колбэк",
                peer_id=event.object.peer_id,
            )

    async def handle_updates(self, updates: list[Update]):
        btn2 = VkButton(label="Стоп игра", color="primary")
        btn1 = VkButton(label="Callaback stop", type_btn="callback")
        # Клавиатура начала игры
        vk_keyboard_start_game = VkKeyboard(one_time=True, inline=False)
        await vk_keyboard_start_game.add_line([btn1.get(), btn2.get()])

        for update in updates:
            if update.object.message.text.upper() == "СТАРТ":
                self.game_on = True
                await self.app.store.vk_api.send_message_with_keyboard(
                    SendMessageWithKeyboard(
                        peer_id=update.object.message.peer_id,
                        text="Начали игру",
                        keyboard=await vk_keyboard_start_game.get_keyboard(),
                    )
                )
            if update.object.message.text.lower() in {
                "[club225776298|@club225776298] стоп игра!",
                "стоп игра!",
                "стоп",
            }:
                self.game_on = False
                await self.app.store.vk_api.send_message_with_keyboard(
                    SendMessageWithKeyboard(
                        peer_id=update.object.message.peer_id,
                        text="Игра окончены, всем спасибо",
                        keyboard=await VkKeyboard().get_keyboard(),
                    ),
                )
                await self.app.store.vk_api.unpin_message(
                    peer_id=update.object.message.peer_id
                )
            if self.game_on:
                await self.app.store.vk_api.send_personal_message(
                    SendMessage(
                        peer_id=update.object.message.peer_id,
                        text=f"Ответ: {update.object.message.text}",
                    )
                )
