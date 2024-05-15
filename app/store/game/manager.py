import typing
from logging import getLogger

from app.game.logic import GameLogic
from app.store.vk_api.dataclasses import (
    EventUpdate,
    MessageUpdate,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.logger = getLogger("BotManager")

    async def handle_games(self, game: GameLogic, message: str, user_id: int):
        if message == "start":
            await game.start_game()

        await game.waiting_answer(user_id=user_id, answer=message)


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.logger = getLogger("BotManager")
        self.games = {}

    async def handle_events(self, events: list[EventUpdate]):
        """Обработка callback событий"""
        for event in events:
            conversation_id = event.object.peer_id
            payload_text = event.object.payload.text
            user_id = event.object.user_id
            event_id = event.object.event_id

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
            if len(self.games) == 0:
                await self.setup_game_store()

            if conversation_id in self.games:
                self.logger.info(self.games[conversation_id])
                game = self.games[conversation_id]
                await self.app.store.game_manager.handle_games(
                    game=game, message=message, user_id=from_id
                )
            else:
                new_game_model = await self.app.store.game_accessor.add_game(
                    peer_id=conversation_id
                )
                new_game_model = (
                    await self.app.store.game_accessor.get_game_by_id(
                        new_game_model.id
                    )
                )
                new_game_logic = GameLogic(
                    app=self.app,
                    game_model=new_game_model,
                )

                self.games[conversation_id] = new_game_logic
                self.logger.info(
                    "Создаем новую модель игры \n %s", new_game_logic
                )

                await self.app.store.game_manager.handle_games(
                    game=new_game_logic, message=message, user_id=from_id
                )

            if message == "/stop":
                cansel_game: GameLogic = self.games.pop(conversation_id)
                await cansel_game.cancel_game()

    async def setup_game_store(self):
        """Загрузка игр в словарь"""
        self.logger.info("Инициализируем загрузку игр в БД")
        games: [
            GameManager
        ] = await self.app.store.game_accessor.get_active_games()
        for game in games:
            new_game = GameLogic(
                app=self.app,
                game_model=game,
            )
            self.games[new_game.conversation_id] = new_game
