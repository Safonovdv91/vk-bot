import typing
from abc import ABC, abstractmethod
from logging import getLogger

from app.games.blitz.logic import AbstractGame, BlitzGameStage, GameBlitz
from app.store.vk_api.dataclasses import (
    EventUpdate,
    MessageUpdate,
)

if typing.TYPE_CHECKING:
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
        """Функция обработки сообщения
        message: - текст сообщения
        user_id: - id пользователя(от которого пришло сообщение)
        """

    @abstractmethod
    async def _load_game_to_inner_memeory(self):
        "Загружаем игру в словарь игр, чтобы не дергать БД постоянно"


class GameManager(AbstractGameManager):
    """Класс менеджера игры"""

    def __init__(self, app: "Application"):
        self.app = app
        self.logger = getLogger(__name__)
        self.logger.info("Инициализирован GameManager")
        self._active_games = {}

    async def _take_active_game_in_chat(
        self, conversation_id: int
    ) -> AbstractGame | None:
        """Возвращает активную игру в чат, если она есть, иначе None"""
        if not self._active_games:
            self.logger.info("Нет активных игр в inner_memory")
            for game in await self.app.store.game_accessor.get_active_games():
                self._active_games[game.conversation_id] = game

        game_manager = self._active_games.get(conversation_id)
        if game_manager:
            return game_manager

        return None

    async def _load_game_to_inner_memeory(self):
        self.logger.info("Загружаем активные игру в словарь игр")
        self.games = await self.app.store.game_accessor.get_active_games()
        self.logger.info("Игры загружены:")
        self.logger.info(self.games)

    async def _start_game(self, conversation_id: int, game: AbstractGame):
        self.logger.info("[%s] Начало игры : начато", conversation_id)
        self._active_games[conversation_id] = game
        await game.start_game()
        self.logger.info("[%s] Начало игры : выполнено", conversation_id)
        return self

    async def _stop_game(self, conversation_id: int, game: AbstractGame):
        self.logger.info("[%s] Конец игры игры : начато", conversation_id)
        await game.stop_game()
        self._active_games.pop(conversation_id)
        self.logger.info("[%s] Конец игры игры : выполнено", conversation_id)
        return True

    async def _pause_game(self, conversation_id: int, game: AbstractGame):
        self.logger.info("[%s] Пауза игры : начато", conversation_id)
        await game.pause_game()
        self.logger.info("[%s] Пауза игры : выполнено", conversation_id)
        return True

    async def _resume_game(self, conversation_id: int, game: AbstractGame):
        self.logger.info("[%s] Продолжение игры : начато", conversation_id)
        await game.resume_game()
        self._active_games[conversation_id] = game
        self.logger.info("[%s] Продолжение игры : выполнено", conversation_id)
        return True

    async def _finish_game(self, conversation_id: int, game: AbstractGame):
        self.logger.info("[%s] Финиш игры : начато", conversation_id)
        await game.finish_game()
        self._active_games[conversation_id] = game
        self.logger.info("[%s] Финиш игры : выполнено", conversation_id)
        return True

    async def handle_message(self, message, user_id, conversation_id):
        self.logger.info("игра ловит сообщение %s от юзера %s", message, user_id)
        game: AbstractGame = self._active_games.get(conversation_id)

        if game and game.game_stage not in [
            BlitzGameStage.FINISHED,
            BlitzGameStage.CANCELED,
        ]:
            if message == "/start_blitz":
                self.logger.info("Сейчас игра уже запущена: %s", game)
                await self.app.store.vk_api.send_message(
                    user_id, "Сейчас игра уже запущена"
                )
            elif message == "/stop":
                return await self._stop_game(conversation_id, game)

            elif message == "/pause":
                await self._pause_game(conversation_id, game)

            elif message == "/resume":
                await self._resume_game(conversation_id, game)

            elif message == "/finish":
                await self._finish_game(conversation_id, game)

            else:
                return await game.handle_message(message, user_id, conversation_id)
        elif message == "/start_blitz":
            theme_id = 1
            offset = 0
            limit = 10
            questions = await self.app.store.blitzes.get_questions_list(
                theme_id, offset, limit
            )
            game = GameBlitz(
                self.app,
                conversation_id=conversation_id,
                admin_id=user_id,
                questions=questions,
            )
            return await self._start_game(conversation_id, game)

        return False


class BotManager:
    """Класс обработки сообщений бота"""

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
            except Exception:
                self.logger.exception("Ошибка при обработке эвента сообщения")

    async def handle_updates(self, updates: list[MessageUpdate]):
        """Обработка пришедших сообщений от пользователей"""
        for update in updates:
            conversation_id = update.object.message.peer_id
            message = update.object.message.text
            from_id = update.object.message.from_id
            try:
                await self.app.store.vk_messages.add_message(
                    conversation_id=conversation_id,
                    text=message,
                    user_id=from_id,
                )
                if await self.app.store.game_manager.handle_message(
                    message=message, user_id=from_id, conversation_id=conversation_id
                ):
                    return

            except Exception:
                self.logger.exception("Ошибка при обработке сообщения")
