import typing
from abc import ABC, abstractmethod
from logging import getLogger

from app.games.game_100.constants import GameStage
from app.store.vk_api.dataclasses import (
    EventUpdate,
    MessageUpdate,
)

if typing.TYPE_CHECKING:
    from app.games.game_100.logic import Game100Logic
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.logger = getLogger(__name__)
        self.games: dict = {}

    async def handle_events(self, events: list[EventUpdate]):
        """Обработка callback событий - событий при нажатие на кнопки"""
        for event in events:
            conversation_id = event.object.peer_id
            payload_text = event.object.payload.text
            user_id = event.object.user_id
            event_id = event.object.event_id

            if not self.games:
                await self.setup_game_store()

            try:
                game = self.games[conversation_id]

                if payload_text == "/reg_on":
                    await game.register_player(event_id=event_id, user_id=user_id)
                elif payload_text == "/reg_off":
                    await game.unregister_player(event_id=event_id, user_id=user_id)
                elif payload_text == "/give_answer":
                    await game.waiting_ready_to_answer(event_id=event_id, user_id=user_id)

            except KeyError:
                self.logger.error("Пришло эвент сообщение в несуществующую игру")

    async def handle_updates(self, updates: list[MessageUpdate]):
        """Обработка пришедших сообщений от пользователей"""
        # todo Необходимо разбить его на несколько этапов
        for update in updates:
            conversation_id = update.object.message.peer_id
            message = update.object.message.text
            from_id = update.object.message.from_id

            await self.app.store.vk_messages.add_message(
                conversation_id=conversation_id,
                text=message,
                user_id=from_id,
            )
            # Проверка на существование игры
            if not self.games:  # Есть ли вообще игры
                await self.setup_game_store()
            # Если игра не отмененная и не финишированная то значит она запущена
            # и надо запускать ее логику

            if conversation_id in self.games and self.games[
                conversation_id
            ].game_state not in (GameStage.CANCELED, GameStage.FINISHED):
                self.logger.info(self.games[conversation_id])

            else:
                game = await self.app.store.game_accessor.add_game(
                    peer_id=conversation_id
                )

                if game is None:
                    self.logger.error("Не удалось создать игру")
                    await self.app.store.vk_api.send_message(
                        text="Не удалось создать игру т.к. нет вопросов в БД",
                        peer_id=conversation_id,
                    )
                    return

                game = await self.app.store.game_accessor.get_game_by_id(game.id)
                new_game_100_1 = Game100Logic(
                    app=self.app,
                    game_model=game,
                )

                self.games[conversation_id] = new_game_100_1
                self.logger.info("Создаем новую модель игры \n %s", new_game_100_1)

            game = self.games[conversation_id]
            if message == "/start_100":
                await game.start_game(admin_id=from_id)

            await game.waiting_answer(user_id=from_id, answer=message)

            if message == "/stop":
                cansel_game: Game100Logic = self.games[conversation_id]

                if await cansel_game.cancel_game(from_id):
                    self.games.pop(conversation_id)

            if message == "/finish":
                cansel_game: Game100Logic = self.games[conversation_id]

                if await cansel_game.end_game(from_id):
                    self.games.pop(conversation_id)

    async def setup_game_store(self):
        """Загрузка игр в словарь"""
        self.logger.info("Инициализируем загрузку игр в БД")
        for game in await self.app.store.game_accessor.get_active_games():
            self.games[
                Game100Logic(
                    app=self.app,
                    game_model=game,
                ).conversation_id
            ] = Game100Logic(
                app=self.app,
                game_model=game,
            )


class AbstractGameManager(ABC):
    """Класс для работы с играми
    Принцип работы.
    при инициализации проверяется списко игр, если пустой -
    скорее всего бот перезапущен.
    Если список пустой, то загружаем игры в словарь из БД.

    При получении сообщения проверяем есть ли игра в словаре, если нет
    - создаем новую игру.
    При получении callback события проверяем есть ли игра в словаре, если нет
    - создаем новую игру.

    Если игра есть  - то проверяем
    """

    def __init__(self, app: "Application"):
        self.app = app
        self.logger = getLogger(__name__)
        self.games: dict = {}

    @abstractmethod
    async def start_game(self):
        self.logger.info("Начинаем игру")

    @abstractmethod
    async def stop_game(self):
        self.logger.info("Останавливаем игру")

    @abstractmethod
    async def finish_game(self):
        self.logger.info("Завершаем игру")

    @abstractmethod
    async def cancel_game(self):
        self.logger.info("Отменяем игру")

    @abstractmethod
    async def pause_game(self):
        self.logger.info("Приостанавливаем игру")

    @abstractmethod
    async def resume_game(self):
        self.logger.info("Возобновляем игру")

    @abstractmethod
    async def _load_game_to_inner_memeory(self, events: list[EventUpdate]):
        """Загрузка игр в словарь из БД"""


class GameManager(AbstractGameManager):
    def __init__(self, app: "Application"):
        super().__init__(app)
        self.logger = getLogger(__name__)
        self.games: dict = {}

    async def start_game(self):
        pass
