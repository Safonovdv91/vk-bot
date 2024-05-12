import random
import typing
from logging import getLogger

from app.game.game_logic import GameLogic
from app.game.models import GameStage
from app.store.game.constants import VkButtons
from app.store.vk_api.dataclasses import (
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

    async def handle_events(self, events: list[Update]):
        """Обработка callback событий """
        self.logger.info("Инфа", extra=dict(name_class=events))
        self.logger.info("Получены события \n %s", events)
        for event in events:
            if event.object.payload.text == "Give answer":
                """
                Если статус игры ожидаю кнопку - переводим в режим
                ожидаю ответ от игрока (id игрока в игре)
                """
                player = await self.app.store.vk_api.get_vk_user(event.object.user_id)

                await self.app.store.vk_api.send_message(
                    peer_id=event.object.peer_id,
                    text=f"Ожидаем ответ от игрока {player.first_name} {player.last_name}",
                )

    async def handle_updates(self, updates: list[Update]):
        btn2 = VkButtons.BTN_ANSWER.value

        # Клавиатура начала игры
        vk_keyboard_start_game = VkKeyboard(one_time=True, inline=False)
        await vk_keyboard_start_game.add_line([btn2.get()])

        for update in updates:
            # Получаем сообщение из группы
            # проверяем есть ли в этой беседе какая либо игра.
            games = await self.app.store.game_manager.get_games_by_peer_id(
                peer_id=update.object.message.peer_id
            )
            print("Передаем update в обработчик игры")
            print(games)



            if games:
                # Проверяем статус игры
                # если игра есть и статус ожидаю сообщения от игрока
                # сверяем answered_player_id и from_id
                pass

            if update.object.message.text.upper() == "СТАРТ":
                for game in games:
                    if game.game_stage == GameStage.WAITING_CALLBACK:
                        await self.app.store.vk_api.send_message(
                            peer_id=update.object.message.peer_id,
                            text="Игра уже идет, ждет коллбэка",
                        )
                        break
                    if game.game_stage == GameStage.WAITING_ANSWER:
                        await self.app.store.vk_api.send_message(
                            peer_id=update.object.message.peer_id,
                            text=f"Игра уже идет, ждет ответа игрока {game.responsed_player_id}",
                        )
                        break
                    await self.app.store.game_manager.add_game(
                        peer_id=update.object.message.peer_id,
                        question_id=game.question_id,
                        game_stage=GameStage.WAITING_CALLBACK,
                    )

                    question = await self.app.store.quizzes.get_question_by_id(game.question_id)
                    await self.app.store.vk_api.send_message(
                        peer_id=update.object.message.peer_id,
                        text=question.title,
                        keyboard=await vk_keyboard_start_game.get_keyboard()
                    )
