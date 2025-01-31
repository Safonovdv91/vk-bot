import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass
from logging import getLogger

from app.blitz.models import GameBlitzQuestion
from app.games.blitz.constants import BlitzGameStage
from app.store.vk_api.dataclasses import VkUser

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

    def __init__(self):
        self.game_stage = None

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
    user: VkUser
    user_score: int = 0


class GameBlitz(AbstractGame):
    def __init__(
        self,
        app: "Application",
        game_id: int | None = None,
        game_stage: BlitzGameStage = BlitzGameStage.WAITING_ANSWER,
        conversation_id: int | None = None,
        admin_id: int = 13007796,
        questions: list[GameBlitzQuestion] | None = None,
    ):
        super().__init__()
        self.game_id = game_id
        self.app = app
        self.logger = getLogger(__name__)
        self.game_stage = game_stage
        self.logger.info("Инициализирован GameBlitz")
        self.conversation_id = conversation_id
        self.admin_id = admin_id
        self.questions: list = questions
        self.id_current_question: int = 0
        self.list_gamers: list[BlitzGameUser] = []

    @property
    def conversation_id(self) -> int | str:
        return self._conversation_id

    @conversation_id.setter
    def conversation_id(self, value: int):
        """Устанавливает conversation_id"""
        if value is None:
            raise ValueError("conversation_id не может быть None") from ValueError
        try:
            v = int(value)
        except ValueError:
            raise ValueError("conversation_id должен быть int") from ValueError
        if v <= 0:
            raise ValueError("conversation_id должен быть > 0") from ValueError

        self._conversation_id = v

    @property
    def admin_id(self):
        return self._admin_id

    @admin_id.setter
    def admin_id(self, value: int):
        if value is None:
            self.logger.info("admin_id is None")
            self._admin_id = None
            return

        try:
            v = int(value)
        except ValueError:
            raise ValueError("admin_id должен быть int") from ValueError

        if v <= 0:
            raise ValueError("admin_id должен быть > 0") from ValueError
        self._admin_id = v

    def _is_true_answer(self, question_id: int, answer: str) -> bool:
        return answer.lower() == self.questions[question_id].answer.lower()

    async def _add_point_score_to_user(self, user_id: int) -> BlitzGameUser:
        """Добавляет пользователю 1 побденое очко"""
        for user in self.list_gamers:
            if user.user.id == user_id:
                user.user_score += 1
                return user

        self.logger.info("Новый игрок")
        user = await self.app.store.vk_api.get_vk_user(user_id)
        blitz_game_user = BlitzGameUser(user=user, user_score=1)
        self.list_gamers.append(blitz_game_user)
        return blitz_game_user

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

    async def handle_message(
        self, message: str | None, user_id: int, conversation_id: int
    ):
        self.logger.info("Обработка сообщения и логики бота")
        if message is None:
            raise TypeError("message не может быть None")
        if user_id is None:
            raise TypeError("user_id не может быть None")
        if conversation_id is None:
            raise TypeError("conversation_id не может быть None")

        if self.game_stage == BlitzGameStage.WAITING_ANSWER:
            self.logger.info("Ожидание ответа")

            if self._is_true_answer(self.id_current_question, message):
                blitz_game_user = await self._add_point_score_to_user(user_id)
                msg = (
                    f"Пользователь {blitz_game_user.user.first_name} дал правильный "
                    f"ответ, у него теперь {blitz_game_user.user_score} очков"
                )
                self.logger.info("[%s]: %s", conversation_id, msg)
                await self.app.store.vk_api.send_message(conversation_id, msg)

                if await self.next_question():
                    return True

                return True

        return False

    async def start_game(self, theme_id: int | None = None):
        if theme_id is None:
            theme_id = 1
            self.logger.info("Тема не задана, по умолчанию - 1")

        self.logger.info("Начало игры")
        self.game_stage = BlitzGameStage.WAITING_ANSWER
        await self.app.store.vk_api.send_message(
            self.conversation_id, "Начата игра BLITZ"
        )
        await self.app.store.vk_api.send_message(
            self.conversation_id, "Будут заданы вопросы"
        )
        self.questions = await self.app.store.blitzes.get_questions_list(theme_id)
        try:
            msg = f"Первый вопрос:\n {self.questions[0].title}"
        except TypeError:
            self.logger.exception("Вопросы не заданы т.к ошибка, ворпосов нет бд")
            await self.cancel_game()
            return False

        await self.app.store.vk_api.send_message(self.conversation_id, msg)
        return True

    async def stop_game(self):
        await self.app.store.blitzes.change_state(
            game_id=self.game_id, new_state=BlitzGameStage.CANCELED
        )
        self.logger.info("Конец игры вызван STOP")
        await self.pause_game()

        return True

    async def finish_game(self):
        self.logger.info("Завершение игры")
        msg = (
            f"Игра успешно завершена!\n"
            f"Вопросов было задано - {self.id_current_question:}\n"
            f"Таблица результатов:\n"
        )
        for _ in self.list_gamers:
            msg += f"|{_.user.first_name} | - {_.user_score} \n"

        await self.app.store.blitzes.change_state(
            game_id=self.game_id, new_state=BlitzGameStage.FINISHED
        )
        await self.app.store.vk_api.send_message(self.conversation_id, msg)
        self.game_stage = BlitzGameStage.FINISHED
        return True

    async def cancel_game(self):
        self.logger.info("Отмена игры")
        self.game_stage = BlitzGameStage.CANCELED
        await self.app.store.blitzes.change_state(
            game_id=self.game_id, new_state=BlitzGameStage.CANCELED
        )
        await self.app.store.vk_api.send_message(self.conversation_id, "Игра отменена")
        return True

    async def pause_game(self):
        self.logger.info("Пауза игры")
        self.game_stage = BlitzGameStage.PAUSE
        await self.app.store.vk_api.send_message(
            self.conversation_id, "Игра приостановлена"
        )
        return True

    async def resume_game(self):
        self.logger.info("Возобновление игры")
        self.game_stage = BlitzGameStage.WAITING_ANSWER
        await self.app.store.vk_api.send_message(
            self.conversation_id, "Игра Возобновлена"
        )
        return True
