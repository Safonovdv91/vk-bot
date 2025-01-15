import typing
from abc import ABC, abstractmethod
from enum import Enum
from logging import getLogger

from app.games.game_100.constants import GameStage
from app.store.vk_api.dataclasses import (
    EventUpdate,
    MessageUpdate,
)
if typing.TYPE_CHECKING:
    from app.games.game_100.logic import Game100Logic
    from app.web.app import Application


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

    @abstractmethod
    async def handle_message(self, message: str, user_id: int, conversation_id: int):
        """ "Функция обработки сообщения
        message: - текст сообщения
        user_id: - id пользователя(от которого пришло сообщение)
        """

    @abstractmethod
    async def _load_game_to_inner_memeory(self):
        "Загружаем игру в словарь игр, чтобы не дергать БД постоянно"


class AbstractGame(ABC):
    """Абстрактный класс игр, содержит логику игры.
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

    @abstractmethod
    async def start_game(self):
        "Функция начала игры"

    @abstractmethod
    async def stop_game(self):
        "Функция остановки игры"

    @abstractmethod
    async def finish_game(self):
        "Функция завершения игры игра записывается в БД как успешно завершенная"

    @abstractmethod
    async def cancel_game(self):
        "Функция отмены игры, игра записывается в БД как неудачная"

    @abstractmethod
    async def pause_game(self):
        "Приостанавливаем игру"

    @abstractmethod
    async def resume_game(self):
        "Возобновляем игру"

    @abstractmethod
    def handle_message(self, message: str, user_id: int, conversation_id: int):
        """ECho залупа"""
        pass

class BlitzGameStage(Enum):
    WAIT_ANSWER  = "WAIT_ANSWER"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"
    CANCELED = "CANCELED"


class GameBlitz(AbstractGame):
    def __init__(self, app: "Application", game_stage: BlitzGameStage = BlitzGameStage.WAIT_ANSWER):
        self.app = app
        self.logger = getLogger(__name__)
        self._game_stage = game_stage
        self.logger.info("Инициализирован GameBlitz")

    async def handle_message(self, message: str, user_id: int, conversation_id: int):
        #todo echo-бот шлет что-то
        self.logger.info("Обработка сообщения и логики бота")
        if self._game_stage == BlitzGameStage.WAIT_ANSWER:
            self.logger.info("Ожидание ответа")
            self.app.store.vk_api.send_message(user_id, message)
            return True
        else:
            self.logger.info("Игра не в ожидании ответа")
            return False

    async def start_game(self):
        self.logger.info("Начало игры")
        self._game_stage = BlitzGameStage.WAIT_ANSWER
        return True

    async def stop_game(self):
        self.logger.info("Конец игры")
        self._game_stage = BlitzGameStage.FINISHED
        return True

    async def finish_game(self):
        self.logger.info("Завершение игры")
        self._game_stage = BlitzGameStage.FINISHED
        return True

    async def cancel_game(self):
        self.logger.info("Отмена игры")
        self._game_stage = BlitzGameStage.CANCELED
        return True


class GameManager(AbstractGameManager):
    """ Класс менеджера игры"""
    def __init__(self, app: "Application"):
        self.app = app
        self.logger = getLogger(__name__)
        self.logger.info("Инициализирован GameManager")
        self._active_games = {}

    async def _take_active_game_in_chat(self,conversation_id :int) -> AbstractGame | None:
        """ Возвращает активную игру в чат, если она есть, иначе None"""
        if not self._active_games:
            self.logger.info("Нет активных игр в inner_memory")
            for game in await self.app.store.game_accessor.get_active_games():
                self._active_games[game.conversation_id] = game

        game_manager = self._active_games.get(conversation_id)
        if game_manager:
            return game_manager
        else:
            return None

    async def _load_game_to_inner_memeory(self):
        self.logger.info("Загружаем активные игру в словарь игр")
        self.games = await self.app.store.game_accessor.get_active_games()
        self.logger.info("Игры загружены:")
        self.logger.info(self.games)

    async def start_game(self,conversation_id: int,game: AbstractGame):
        self.logger.info("[%s]Начало игры : начато", conversation_id)
        self._active_games[conversation_id] = game
        # todo добавить БД игру
        await game.start_game()

        self.logger.info("[%s]Начало игры : выполнено", conversation_id)
        return self

    async def stop_game(self,conversation_id: int, game: AbstractGame):
        self.logger.info("[%s]Конец игры игры : начато", conversation_id)
        await game.stop_game()
        self._active_games.pop(conversation_id)
        self.logger.info("[%s]Конец игры игры : выполнено", conversation_id)
        return True

    async def handle_message(self, message, user_id, conversation_id):
        self.logger.info("игра ловит сообщение %s от юзера %s", message, user_id)
        # todo вызов функции остановки выбранной игры
        if message == "/start_blitz":
            game = GameBlitz(self.app)
            await self.start_game(conversation_id, game)
            return True

        elif message == "/stop_blitz":
            game = await self._active_games.get(conversation_id)
            if game:
                await self.stop_game(conversation_id, game)
            else:
                self.logger.info("Нет активной игры")
                return False
            return True
        else:
            self.logger.info("Неизвестная команда")
            await self.app.store.vk_api.send_message(
                peer_id=conversation_id,
                text=f"Неизвестная команда"
            )
            return False

class BotManager:
    """ Класс обработки сообщений бота"""
    def __init__(self, app: "Application"):
        self.app = app
        self.logger = getLogger(__name__)
        self.games: dict = {}
        # todo при инициализации проверка на существуют ли игры

    async def handle_events(self, events: list[EventUpdate]):
        """Обработка callback событий - событий при нажатие на кнопки"""
        for event in events:
            conversation_id = event.object.peer_id
            payload_text = event.object.payload.text
            user_id = event.object.user_id
            event_id = event.object.event_id

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

            # Добавляем сообщение в БД для хранения
            await self.app.store.vk_messages.add_message(
                conversation_id=conversation_id,
                text=message,
                user_id=from_id,
            )
            game_manager = self.app.store.game_manager
            await game_manager.handle_message(message=message, user_id=from_id, conversation_id=conversation_id)

            #
            # if conversation_id in self.games and self.games[
            #     conversation_id
            # ].game_state not in (GameStage.CANCELED, GameStage.FINISHED):
            #     self.logger.info(self.games[conversation_id])
            #
            # else:
            #     game = await self.app.store.game_accessor.add_game(
            #         peer_id=conversation_id
            #     )
            #
            #     if game is None:
            #         self.logger.error("Не удалось создать игру")
            #         await self.app.store.vk_api.send_message(
            #             text="Не удалось создать игру т.к. нет вопросов в БД",
            #             peer_id=conversation_id,
            #         )
            #         return
            #
            #     game = await self.app.store.game_accessor.get_game_by_id(game.id)
            #     new_game_100_1 = Game100Logic(
            #         app=self.app,
            #         game_model=game,
            #     )
            #
            #     self.games[conversation_id] = new_game_100_1
            #     self.logger.info("Создаем новую модель игры \n %s", new_game_100_1)
            #
            # game = self.games[conversation_id]
            # if message == "/start_100":
            #     await game.start_game(admin_id=from_id)
            #
            # await game.waiting_answer(user_id=from_id, answer=message)
            #
            # if message == "/stop":
            #     cansel_game: Game100Logic = self.games[conversation_id]
            #
            #     if await cansel_game.cancel_game(from_id):
            #         self.games.pop(conversation_id)
            #
            # if message == "/finish":
            #     cansel_game: Game100Logic = self.games[conversation_id]
            #
            #     if await cansel_game.end_game(from_id):
            #         self.games.pop(conversation_id)
