import asyncio
import typing
from abc import ABC, abstractmethod
from enum import Enum
from logging import getLogger

if typing.TYPE_CHECKING:
    from app.games.game_100.logic import Game100Logic
    from app.web.app import Application


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
    WAIT_ANSWER = "WAIT_ANSWER"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"
    CANCELED = "CANCELED"


class GameBlitz(AbstractGame):
    def __init__(
        self,
        app: "Application",
        game_stage: BlitzGameStage = BlitzGameStage.WAIT_ANSWER,
        conversation_id: int = None,
        admin_id: int = None,
    ):
        self.app = app
        self.logger = getLogger(__name__)
        self._game_stage = game_stage
        self.logger.info("Инициализирован GameBlitz")
        self.conversation_id = conversation_id
        self.admin_id = admin_id
        self.questions: list = []

    async def handle_message(self, message: str, user_id: int, conversation_id: int):
        # todo echo-бот шлет что-то
        self.logger.info("Обработка сообщения и логики бота")

        if self._game_stage == BlitzGameStage.WAIT_ANSWER:
            self.logger.info("Ожидание ответа")
            await self.app.store.vk_api.send_message(user_id, message)
            return True
        else:
            self.logger.info("Игра не в ожидании ответа")
            return False

    async def start_game(self):
        self.logger.info("Начало игры")
        self._game_stage = BlitzGameStage.WAIT_ANSWER
        await self.app.store.vk_api.send_message(
            self.conversation_id, "Начата игра BLITZ"
        )
        await asyncio.sleep(2)
        await self.app.store.vk_api.send_message(
            self.conversation_id, "Будут заданы вопросы"
        )
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

    async def pause_game(self):
        self.logger.info("Пауза игры")
        self._game_stage = BlitzGameStage.PAUSED
        await self.app.store.vk_api.send_message(
            self.conversation_id, "Игра приостановлена"
        )
        return True

    async def resume_game(self):
        self.logger.info("Возобновление игры")
        self._game_stage = BlitzGameStage.WAIT_ANSWER
        await self.app.store.vk_api.send_message(
            self.conversation_id, "Игра Возобновлена"
        )

        return True
