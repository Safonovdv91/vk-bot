import typing
from abc import ABC, abstractmethod
from logging import getLogger

from aiohttp.web_exceptions import HTTPBadRequest, HTTPConflict, HTTPNotFound

from app.games.blitz.logic import AbstractGame, BlitzGameStage, GameBlitz
from app.games.blitz.models import BlitzGame
from app.store.vk_api.dataclasses import (
    EventUpdate,
    MessageUpdate,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Observer(ABC):
    @abstractmethod
    async def handle_message_update(self, update: MessageUpdate):
        pass


class VkPopUpNotifire(Observer):
    def __init__(self, app: "Application"):
        self.app = app
        self.logger = getLogger(__name__)

    async def handle_message_update(self, update: MessageUpdate) -> None:
        self.logger.debug(
            "[%s] Notify: Обработка сообщения: [%s]",
            update.object.message.conversation_message_id,
            update.object.message.text,
        )
        await self.app.store.vk_api.send_message(
            update.object.message.peer_id, text=f"ECHO: {update.object.message.text}"
        )


class VkGameMessageHandler(Observer):
    def __init__(self, app: "Application"):
        self.app = app
        self.logger = getLogger(__name__)

    async def handle_message_update(self, update: MessageUpdate) -> None:
        self.logger.debug(
            "[%s]GAME: Обработка сообщения: [%s]",
            update.object.message.conversation_message_id,
            update.object.message.text,
        )
        conversation_id = update.object.message.peer_id
        message = update.object.message.text
        from_id = update.object.message.from_id
        try:
            await self.app.store.game_manager.handle_message(
                message=message, user_id=from_id, conversation_id=conversation_id
            )

        except Exception:
            self.logger.exception("Ошибка при обработке сообщения")


class DbMessageSaver(Observer):
    def __init__(self, app: "Application"):
        self.app = app
        self.logger = getLogger(__name__)

    async def handle_message_update(self, update: MessageUpdate) -> None:
        self.logger.debug(
            "[%s]DB: сохраняем сообщение: [%s]",
            update.object.message.conversation_message_id,
            update.object.message.text,
        )
        conversation_id = update.object.message.peer_id
        message = update.object.message.text
        from_id = update.object.message.from_id
        try:
            await self.app.store.vk_messages.add_message(
                conversation_id=conversation_id,
                text=message,
                user_id=from_id,
            )
        except Exception:
            self.logger.exception("Ошибка при обработке сообщения")


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
    async def _load_game_to_inner_memory(self):
        "Загружаем игру в словарь игр, чтобы не дергать БД постоянно"


class GameManager(AbstractGameManager):
    """Класс менеджера игры"""

    def __init__(self, app: "Application"):
        self.app = app
        self.logger = getLogger(__name__)
        self.logger.info("Инициализирован GameManager")
        self._active_games: dict = {}

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

    async def _load_game_to_inner_memory(self):
        self.games = []
        self._active_games = {}
        blitz_db_games = await self.app.store.blitzes.get_active_games()
        blitz_games = [
            GameBlitz(
                self.app,
                game_id=game.id,
                game_stage=game.game_stage,
                conversation_id=game.conversation_id,
                admin_id=game.admin_game_id,
            )
            for game in blitz_db_games
        ]

        for game in blitz_games:
            self._active_games[game.conversation_id] = game

        self.logger.info("Игры загружены в inner_memory")
        self.logger.info("Игры в inner_memory : %s", self._active_games)

    async def _start_game(self, conversation_id: int, game: AbstractGame) -> None:
        self.logger.info("[%s] Начало игры : начато", conversation_id)
        self._active_games[conversation_id] = game
        # todo accessor добавления начала игры в БД
        bd_game = await self.app.store.blitzes.add_game(
            conversation_id=game.conversation_id,
            theme_id=game.theme_id,
            admin_game_id=game.admin_id,
        )
        game.game_id = bd_game.id
        game.game_model = bd_game
        await game.start_game()

        self.logger.info("[%s] Начало игры : выполнено", conversation_id)

    async def _stop_game(self, conversation_id: int, game: AbstractGame):
        self.logger.info("[%s] Конец игры игры : начато", conversation_id)
        await self.app.store.blitzes.change_state(
            game_id=self._active_games[conversation_id].game_model.id,
            new_state=BlitzGameStage.FINISHED.value,
        )
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

    async def start_game(
        self,
        conversation_id: int,
        theme_id: int | None = None,
        admin_id: int | None = None,
    ) -> bool:
        self.logger.info(
            "Запуск игры в чате %s\ntheme id: [ %s ]\nadmin id: [ %s ]",
            conversation_id,
            theme_id,
            admin_id,
        )
        if self._active_games is None:
            await self._load_game_to_inner_memory()

        if self._active_games.get(conversation_id):
            self.logger.warning("Игра уже запущена")
            raise HTTPConflict(reason="Игра уже запущена")

        if theme_id is None:
            theme_id = 1
        if conversation_id is None:
            raise HTTPBadRequest(reason="conversation_id is None")
        if admin_id is None:
            admin_id = 13007796

        theme_id = int(theme_id)
        conversation_id = int(conversation_id)
        admin_id = int(admin_id)

        game = GameBlitz(
            self.app,
            conversation_id=conversation_id,
            admin_id=admin_id,
        )
        game.theme_id = theme_id

        await self._start_game(conversation_id, game)

        return True

    async def pause_game(
        self,
        conversation_id: int,
    ) -> None:
        active_game = self._active_games.get(conversation_id)
        if active_game is None:
            self.logger.info("Игра в чате %s нет", conversation_id)
            raise HTTPNotFound(reason="Игра сейчас не идет")

        self.logger.info("Пауза игры в чате %s", conversation_id)
        await self._pause_game(conversation_id, active_game)

    async def resume_game(self, game_model: BlitzGame) -> None:
        active_game = self._active_games.get(game_model.conversation_id)
        if active_game is None:
            game = GameBlitz(
                self.app,
                conversation_id=game_model.conversation_id,
                admin_id=game_model.admin_game_id,
                game_id=game_model.id,
                game_stage=BlitzGameStage.WAITING_ANSWER,
                questions=game_model.theme.questions,
            )
            self._active_games[game_model.conversation_id] = game

            self.logger.info("Игры в чате %s нет", game_model.conversation_id)
            raise HTTPNotFound(
                reason="Игра сейчас не идет, возможно была"
                " перезагрузка, иницилизировали заново"
            )

        active_game = self._active_games.get(game_model.conversation_id)
        self.logger.info("продолжаем игру в чате %s", active_game.conversation_id)
        await self.app.store.vk_api.send_message(
            peer_id=active_game.conversation_id, message="Продолджаем игру"
        )

    async def finish_game(
        self,
        conversation_id: int,
    ) -> None:
        active_game = self._active_games.get(conversation_id)
        if active_game is None:
            self.logger.info("Игра в чате %s нет", conversation_id)
            raise HTTPNotFound(reason="Игра сейчас не идет, возможно была перезагрузка")

        self.logger.info("Пауза игры в чате %s", conversation_id)

    async def cancel_game(
        self,
        conversation_id: int,
    ) -> None:
        active_game = self._active_games.get(conversation_id)
        if active_game is None:
            self.logger.info("Игра в чате %s нет", conversation_id)
            raise HTTPNotFound(reason="Игра сейчас не идет, возможно была перезагрузка")

        self.logger.info("Отмена игры в чате %s", conversation_id)
        self._active_games.pop(conversation_id)

    async def handle_message(self, message, user_id, conversation_id):
        self.logger.info("игра ловит сообщение %s от юзера %s", message, user_id)
        if self._active_games is None:
            await self._load_game_to_inner_memory()

        game: AbstractGame = self._active_games.get(conversation_id)
        if game and game.game_stage not in [
            BlitzGameStage.FINISHED,
            BlitzGameStage.CANCELED,
        ]:
            methods = {
                "/": self._start_game,
                "/start_blitz": self._start_game,
                "/cancel": self.cancel_game,
                "/pause": self._pause_game,
                "/resume": self._resume_game,
                "/finish": self._finish_game,
            }
            if message in methods:
                self.logger.info("Вызвана команда %s", message)
                return await methods[message](conversation_id, game)

            return await game.handle_message(message, user_id, conversation_id)

        if message == "/start_blitz":
            try:
                await self.start_game(
                    conversation_id=conversation_id, theme_id=None, admin_id=user_id
                )
            except HTTPNotFound as exc:
                await self.app.store.vk_api.send_message(user_id, f"{exc.reason}")
            except HTTPConflict as exc:
                await self.app.store.vk_api.send_message(user_id, f"{exc.reason}")
            except Exception:
                self.logger.exception("Ошибка при запуске игры")

        return False


class BotManager:
    """Класс обработки сообщений бота"""

    def __init__(self, app: "Application"):
        self.app = app
        self.logger = getLogger(__name__)
        self.games: dict = {}
        self.observers = []

        vk_notifire = VkPopUpNotifire(app)
        db_saver = DbMessageSaver(app)
        game_handler = VkGameMessageHandler(app)

        # self.add_observer(vk_notifire)
        self.add_observer(db_saver)
        self.add_observer(game_handler)

    def add_observer(self, observer: Observer):
        self.observers.append(observer)

    def remove_observer(self, observer: Observer):
        self.observers.remove(observer)

    async def notify_observers(self, update: MessageUpdate):
        for observer in self.observers:
            await observer.handle_message_update(update)

    async def new_message(self, update: MessageUpdate):
        await self.notify_observers(update)

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
            await self.new_message(update)
