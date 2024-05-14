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


class GameManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.logger = getLogger("BotManager")

        self.state = GameStage.WAIT_INIT
        self.players_list = []

    async def handle_games(self, game: GameLogic, message: str, user_id: int):
        if game.game_stage.WAIT_INIT and message == "start":
            await game.start_game()

        await game.waiting_answer(user_id=user_id, answer=message)


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
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

            if conversation_id in self.games:
                self.logger.info(self.games[conversation_id])
                game = self.games[conversation_id]
                await self.app.store.game_manager.handle_games(
                    game=game, message=message, user_id=from_id
                )
            else:
                new_game = GameLogic(
                    app=self.app, conversation_id=conversation_id
                )
                self.games[conversation_id] = new_game
                self.logger.info("Создаем новую модель игры \n %s", new_game)
                await self.app.store.game_manager.handle_games(
                    game=new_game, message=message, user_id=from_id
                )
