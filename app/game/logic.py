import asyncio
import typing
from logging import getLogger

from app.game.states import GameStage
from app.store.vk_api.utils import VkButton, VkKeyboard

if typing.TYPE_CHECKING:
    from app.web.app import Application


async def registration_timer(timeout):
    await asyncio.sleep(timeout)


class Game:
    def __init__(self, app: "Application", conversation_id):
        self.app = app
        self.logger = getLogger("BotManager")

        self.players_list = []  # Список игроков
        self.time_to_answer = 15  # время данное на ответ
        self.answers: dict = {"50": 15, "100": 75}
        self.time_to_registration = 15
        self.min_count_gamers: int = 1 # ТЕстовые данные
        self.max_count_gamers: int = 1 # Тестовые данные

        self.conversation_id: int = conversation_id
        self.game_stage: GameStage = GameStage.WAIT_INIT

        self.answered_player = None
        self.pinned_conversation_message_id: int | None = None
        self.question: str | None = "Сколько деняк в кошельке?"
        self.players: list[str] | None = []

    async def get_state(self):
        await self.app.store.vk_api.send_message(
            peer_id=self.conversation_id,
            text=f"Cейчас идет {self.game_stage}",
        )

    async def _start_registration_timer(self, timeout: int):
        await asyncio.create_task(registration_timer(timeout))

        if self.game_stage == GameStage.REGISTRATION_GAMERS:
            if (
                self.min_count_gamers
                < len(self.players)
                < self.min_count_gamers
            ):
                self.game_stage = GameStage.WAITING_READY_TO_ANSWER
                await self.app.store.vk_api.send_message(
                    peer_id=self.conversation_id,
                    text=f"Время на регистрацию закончилось,"
                    f" участвует {len(self.players)} игроков",
                )
            else:
                self.game_stage = GameStage.WAIT_INIT
                await self.app.store.vk_api.send_message(
                    peer_id=self.conversation_id,
                    text=f"Время на регистрацию закончилось,"
                    f" не набралось достаточное количество игроков"
                    f" {len(self.players)}/{self.min_count_gamers}",
                )

    async def start_game(self):
        if self.game_stage == GameStage.WAIT_INIT:
            self.logger.info("START_GAME")
            keyboard_start_game = VkKeyboard(one_time=False, inline=False)
            btn_reg_on = VkButton(
                label="Буду играть",
                type_btn="callback",
                payload={"type": "show_snackbar", "text": "/reg_on"},
                color="primary",
            ).get()
            btn_reg_off = VkButton(
                label="Отменить регистрацию",
                type_btn="callback",
                payload={"type": "show_snackbar", "text": "/reg_off"},
                color="secondary",
            ).get()
            await keyboard_start_game.add_line([btn_reg_on, btn_reg_off])

            await self.app.store.vk_api.send_message(
                peer_id=self.conversation_id,
                text="Началась регистрация на игру!",
                keyboard=await keyboard_start_game.get_keyboard(),
            )
            self.game_stage = GameStage.REGISTRATION_GAMERS

            # timer = self._start_registration_timer(self.time_to_registration)
        else:
            await self.app.store.vk_api.send_message(
                peer_id=self.conversation_id,
                text="Невозможно сейчас начать игру, т.к. она уже идет",
            )

    async def _send_question(self):
        keyboard_start_game = VkKeyboard(one_time=False)
        btn_ready_to_answer = VkButton(
            label="Знаю ответ!",
            type_btn="callback",
            payload={"type": "show_snackbar", "text": "/give_answer"},
            color="primary",
        ).get()

        await keyboard_start_game.add_line([btn_ready_to_answer])

        await self.app.store.vk_api.send_message(
            peer_id=self.conversation_id,
            text=self.question,
            keyboard=await keyboard_start_game.get_keyboard(),
        )

    async def register_player(self, event_id, user_id):
        if self.game_stage == GameStage.REGISTRATION_GAMERS:
            self.logger.info("Регистрируем игрока")

            if user_id not in self.players:
                self.players.append(user_id)

                if len(self.players) >= self.max_count_gamers:
                    self.game_stage = GameStage.WAITING_READY_TO_ANSWER

                    await self.app.store.vk_api.send_message(
                        peer_id=self.conversation_id,
                        text=f"Набралось достаточное количество игроков"
                        f" {len(self.players)}/{self.min_count_gamers}",
                    )
                    await self._send_question()

                await self.app.store.vk_api.send_event_answer(
                    event_id=event_id,
                    peer_id=self.conversation_id,
                    user_id=user_id,
                    response_text="Успешная регистрация!",
                )
            else:
                await self.app.store.vk_api.send_event_answer(
                    event_id=event_id,
                    peer_id=self.conversation_id,
                    user_id=user_id,
                    response_text="Вы уже зарегестрированы!",
                )

    async def unregister_player(self, event_id, user_id):
        if self.game_stage == GameStage.REGISTRATION_GAMERS:
            if user_id in self.players:
                self.players.remove(user_id)
                await self.app.store.vk_api.send_event_answer(
                    event_id=event_id,
                    peer_id=self.conversation_id,
                    user_id=user_id,
                    response_text="Вы отменили регистрацию на игру!",
                )
            else:
                await self.app.store.vk_api.send_event_answer(
                    event_id=event_id,
                    peer_id=self.conversation_id,
                    user_id=user_id,
                    response_text="Вы и не были зареганы!",
                )

        else:
            await self.app.store.vk_api.send_event_answer(
                event_id=event_id,
                peer_id=self.conversation_id,
                user_id=user_id,
                response_text="Набор игроков уже закончился",
            )

    async def waiting_ready_to_answer(self, event_id, user_id):
        if (
            self.game_stage == GameStage.WAITING_READY_TO_ANSWER
            and user_id in self.players
        ):
            self.logger.info("Waiting ready to answer")
            self.game_stage = GameStage.WAITING_ANSWER
            self.answered_player = user_id

            await self.app.store.vk_api.send_event_answer(
                event_id=event_id,
                peer_id=self.conversation_id,
                user_id=user_id,
                response_text=f"Поздравляю, ты отвечаешь на вопрос,"
                f" у тебя {self.time_to_answer} секунд!",
            )
            keyboard_start_game = VkKeyboard(one_time=True)
            await self.app.store.vk_api.send_message(
                peer_id=self.conversation_id,
                text=f"На вопрос отвечает игрок {self.answered_player}",
                keyboard=await keyboard_start_game.get_keyboard(),
            )

        elif self.game_stage == GameStage.WAITING_ANSWER:
            await self.app.store.vk_api.send_event_answer(
                event_id=event_id,
                peer_id=self.conversation_id,
                user_id=user_id,
                response_text="К сожалению не успел!",
            )

        else:
            await self.app.store.vk_api.send_event_answer(
                event_id=event_id,
                peer_id=self.conversation_id,
                user_id=user_id,
                response_text="Уже нет в этом смысла!",
            )

    async def waiting_answer(self, user_id, answer):
        if (
            self.game_stage == GameStage.WAITING_ANSWER
            and user_id == self.answered_player
        ):
            if answer in self.answers:
                await self.app.store.vk_api.send_message(
                    peer_id=self.conversation_id,
                    text=f"Игрок: {self.answered_player} ответил прпавильно"
                    f" и получил {self.answers.pop(answer)} очков!",
                )
                if len(self.answers.keys()) == 0:
                    self.game_stage = GameStage.WAIT_INIT
                    await self.app.store.vk_api.send_message(
                        peer_id=self.conversation_id, text="Игра окончена!"
                    )
                    # Функция окончания игры( подсчета очков, красивого вывода
                else:
                    await self._send_question()
                    self.game_stage = GameStage.WAITING_READY_TO_ANSWER
            else:
                self.game_stage = GameStage.WAITING_READY_TO_ANSWER
                await self._send_question()

    def __repr__(self):
        return f"Это игра из {self.conversation_id}"
