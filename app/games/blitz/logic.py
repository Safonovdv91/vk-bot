import asyncio
import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from logging import getLogger

from app.blitz.models import GameBlitzQuestion

if typing.TYPE_CHECKING:
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
        """Обработка сообщения ботом"""


@dataclass
class BlitzGameUser:
    user_id: int
    user_score: int = 0


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
        conversation_id: int | None = None,
        admin_id: int = 13007796,
        questions: list[GameBlitzQuestion] | None = None,
    ):
        self.app = app
        self.logger = getLogger(__name__)
        self._game_stage = game_stage
        self.logger.info("Инициализирован GameBlitz")
        self.conversation_id = int(conversation_id)
        self.admin_id = int(admin_id)
        self.questions: list = questions
        self.id_current_question: int = 0
        self.list_gamers: list[BlitzGameUser] = []

    def _is_true_answer(self, question_id: int, answer: str) -> bool:
        return answer.lower() == self.questions[question_id].answer.lower()

    def _add_point_score_to_user(self, user_id: int) -> BlitzGameUser:
        """Добавляет пользователю 1 побденое очко"""
        for user in self.list_gamers:
            if user.user_id == user_id:
                user.user_score += 1
                return user

        self.logger.info("Новый игрок")
        user = BlitzGameUser(user_id=user_id, user_score=1)
        self.list_gamers.append(user)
        return user

    async def next_question(self):
        self.logger.info("Следующий вопрос")
        self.id_current_question += 1
        if self.id_current_question < len(self.questions):
            await self.app.store.vk_api.send_message(
                self.conversation_id, self.questions[self.id_current_question].title
            )
            return True

        self.logger.info("Все вопросы заданы")
        await self.finish_game()
        return False

    async def handle_message(self, message: str, user_id: int, conversation_id: int):
        self.logger.info("Обработка сообщения и логики бота")

        if self._game_stage == BlitzGameStage.WAIT_ANSWER:
            self.logger.info("Ожидание ответа")

            if self._is_true_answer(self.id_current_question, message):
                user = self._add_point_score_to_user(user_id)
                msg = (
                    f"Пользователь {user_id} дал правильный ответ,"
                    f" у него теперь {user.user_score} очков"
                )
                self.logger.info("[%s]: %s", conversation_id, msg)
                await self.app.store.vk_api.send_message(conversation_id, msg)

                if await self.next_question():
                    return True

                await self.stop_game()
                return True

        return False

    async def start_game(self):
        self.logger.info("Начало игры")
        self._game_stage = BlitzGameStage.WAIT_ANSWER
        await self.app.store.vk_api.send_message(
            self.conversation_id, "Начата игра BLITZ"
        )
        await asyncio.sleep(1)
        await self.app.store.vk_api.send_message(
            self.conversation_id, "Будут заданы вопросы"
        )
        msg = f"Первый вопрос:\n {self.questions[0].title}"
        await self.app.store.vk_api.send_message(self.conversation_id, msg)
        return True

    async def stop_game(self):
        self.logger.info("Конец игры")
        self._game_stage = BlitzGameStage.FINISHED
        return True

    async def finish_game(self):
        self.logger.info("Завершение игры")
        msg = (
            f"Игра успешно завершена!\n"
            f"вопросов было задано - {len(self.questions)}\n"
            f"таблица результатов:\n {self.list_gamers}"
        )
        for _ in self.list_gamers:
            msg += f"| {_.user_id} | - {_.user_score} \n"

        await self.app.store.vk_api.send_message(self.conversation_id, msg)
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
