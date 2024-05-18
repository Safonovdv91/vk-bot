import typing
from logging import getLogger

from app.game.logic import GameLogic
from app.game.models import GameStage
from app.store.vk_api.dataclasses import (
    EventUpdate,
    MessageUpdate,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.logger = getLogger("BotManager")
        self.games: dict = {}

    async def handle_events(self, events: list[EventUpdate]):
        """Обработка callback событий"""
        for event in events:
            conversation_id = event.object.peer_id
            payload_text = event.object.payload.text
            user_id = event.object.user_id
            event_id = event.object.event_id

            if not self.games:
                await self.setup_game_store()

            game = self.games[conversation_id]

            if payload_text == "/reg_on":
                await game.register_player(event_id=event_id, user_id=user_id)
            elif payload_text == "/reg_off":
                await game.unregister_player(event_id=event_id, user_id=user_id)
            elif payload_text == "/give_answer":
                await game.waiting_ready_to_answer(
                    event_id=event_id, user_id=user_id
                )

    async def handle_updates(self, updates: list[MessageUpdate]):
        """Обработка пришедших сообщений"""
        for update in updates:
            conversation_id = update.object.message.peer_id
            message = update.object.message.text
            from_id = update.object.message.from_id

            if not self.games:
                await self.setup_game_store()

            if conversation_id in self.games and self.games[
                conversation_id
            ].game_state not in (GameStage.CANCELED, GameStage.FINISHED):
                self.logger.info(self.games[conversation_id])
                game = self.games[conversation_id]

            else:
                game = await self.app.store.game_accessor.add_game(
                    peer_id=conversation_id
                )
                game = await self.app.store.game_accessor.get_game_by_id(
                    game.id
                )
                new_game_logic = GameLogic(
                    app=self.app,
                    game_model=game,
                )

                self.games[conversation_id] = new_game_logic
                self.logger.info(
                    "Создаем новую модель игры \n %s", new_game_logic
                )

            game = self.games[conversation_id]
            if message == "/start":
                await game.start_game()

            await game.waiting_answer(user_id=from_id, answer=message)

            if message == "/stop":
                cansel_game: GameLogic = self.games.pop(conversation_id)
                await cansel_game.cancel_game()

    async def setup_game_store(self):
        """Загрузка игр в словарь"""
        self.logger.info("Инициализируем загрузку игр в БД")
        for game in await self.app.store.game_accessor.get_active_games():
            self.games[
                GameLogic(
                    app=self.app,
                    game_model=game,
                ).conversation_id
            ] = GameLogic(
                app=self.app,
                game_model=game,
            )
