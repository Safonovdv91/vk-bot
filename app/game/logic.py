import asyncio
import typing
from logging import getLogger

from app.game.models import Game, GameStage
from app.store.vk_api.dataclasses import VkUser
from app.store.vk_api.utils import VkButton, VkKeyboard

if typing.TYPE_CHECKING:
    from app.web.app import Application


async def registration_timer(timeout):
    await asyncio.sleep(timeout)


class GameLogic:
    def __init__(self, app: "Application", conversation_id, game_model: Game):
        self.game_id = None
        self.app = app
        self.logger = getLogger("BotManager")
        self.game_accessor = self.app.store.game_accessor
        self.vk_accessor = self.app.store.vk_api

        self.players_list = game_model.players  # Список игроков
        self.time_to_answer = 15  # время данное на ответ

        self.answers: dict = {}
        for ans in game_model.question.answers:
            self.answers[ans.title] = ans.score

        self.time_to_registration = 15
        self.min_count_gamers: int = 1  # ТЕстовые данные
        self.max_count_gamers: int = 1  # Тестовые данные

        self.conversation_id: int = game_model.conversation_id
        self.game_state: GameStage = game_model.state

        self.answered_player: VkUser | None = None
        self.answered_player_id: int | None = game_model.responsed_player_id

        self.pinned_conversation_message_id: int | None = None
        self.question: str | None = None
        self.players: list[int] | None = []

        self.game_id = game_model.id
        self.question_id: game_model.question_id

    async def _resend_question(self):
        """Функция повторной отправки вопроса игры

        :return:
        """
        keyboard_start_game = VkKeyboard(one_time=False)
        btn_ready_to_answer = VkButton(
            label="Знаю ответ!",
            type_btn="callback",
            payload={"type": "show_snackbar", "text": "/give_answer"},
            color="primary",
        ).get()

        await keyboard_start_game.add_line([btn_ready_to_answer])
        await self.vk_accessor.send_message(
            peer_id=self.conversation_id,
            text=self.question,
            keyboard=await keyboard_start_game.get_keyboard(),
        )

    async def get_state(self):
        await self.vk_accessor.send_message(
            peer_id=self.conversation_id,
            text=f"Cейчас идет {self.game_state}",
        )

    async def _start_registration_timer(self, timeout: int):
        await asyncio.create_task(registration_timer(timeout))

        if self.game_state == GameStage.REGISTRATION_GAMERS:
            if (
                self.min_count_gamers
                < len(self.players)
                < self.min_count_gamers
            ):
                self.game_state = GameStage.WAITING_READY_TO_ANSWER
                await self.vk_accessor.send_message(
                    peer_id=self.conversation_id,
                    text=f"Время на регистрацию закончилось,"
                    f" участвует {len(self.players)} игроков",
                )

            else:
                self.game_state = GameStage.WAIT_INIT
                await self.vk_accessor.send_message(
                    peer_id=self.conversation_id,
                    text=f"Время на регистрацию закончилось,"
                    f" не набралось достаточное количество игроков"
                    f" {len(self.players)}/{self.min_count_gamers}",
                )

    async def start_game(self):
        if self.game_state == GameStage.WAIT_INIT:
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

            await self.vk_accessor.send_message(
                peer_id=self.conversation_id,
                text="Началась регистрация на игру!",
                keyboard=await keyboard_start_game.get_keyboard(),
            )
            self.game_state = GameStage.REGISTRATION_GAMERS
            await self.game_accessor.change_state(
                game_id=self.game_id, new_state=GameStage.REGISTRATION_GAMERS
            )
            # timer = self._start_registration_timer(self.time_to_registration)
        else:
            await self.vk_accessor.send_message(
                peer_id=self.conversation_id,
                text="Невозможно сейчас начать игру, т.к. она уже идет",
            )

    async def register_player(self, event_id, user_id):
        if self.game_state == GameStage.REGISTRATION_GAMERS:
            self.logger.info("Регистрируем игрока")

            if user_id not in self.players:
                self.players.append(user_id)
                vk_user = await self.vk_accessor.get_vk_user(user_id)
                await self.game_accessor.add_player(
                    game_id=self.game_id,
                    vk_user_id=user_id,
                    name=f"{vk_user.last_name} {vk_user.first_name}",
                )

                if len(self.players) >= self.max_count_gamers:
                    self.game_state = GameStage.WAITING_READY_TO_ANSWER
                    await self.game_accessor.change_state(
                        game_id=self.game_id,
                        new_state=GameStage.WAITING_READY_TO_ANSWER,
                    )

                    await self.vk_accessor.send_message(
                        peer_id=self.conversation_id,
                        text=f"Набралось достаточное количество игроков"
                        f" {len(self.players)}/{self.min_count_gamers}",
                    )
                    await self._resend_question()

                await self.vk_accessor.send_event_answer(
                    event_id=event_id,
                    peer_id=self.conversation_id,
                    user_id=user_id,
                    response_text="Успешная регистрация!",
                )

            else:
                await self.vk_accessor.send_event_answer(
                    event_id=event_id,
                    peer_id=self.conversation_id,
                    user_id=user_id,
                    response_text="Вы уже зарегестрированы!",
                )

    async def unregister_player(self, event_id, user_id):
        if self.game_state == GameStage.REGISTRATION_GAMERS:
            if user_id in self.players:
                self.players.remove(user_id)
                await self.app.store.game_accessor.delete_player(
                    game_id=self.game_id, vk_user_id=user_id
                )

                await self.vk_accessor.send_event_answer(
                    event_id=event_id,
                    peer_id=self.conversation_id,
                    user_id=user_id,
                    response_text="Вы отменили регистрацию на игру!",
                )

            else:
                await self.vk_accessor.send_event_answer(
                    event_id=event_id,
                    peer_id=self.conversation_id,
                    user_id=user_id,
                    response_text="Вы и не были зареганы!",
                )

        else:
            await self.vk_accessor.send_event_answer(
                event_id=event_id,
                peer_id=self.conversation_id,
                user_id=user_id,
                response_text="Набор игроков уже закончился",
            )

    async def waiting_ready_to_answer(self, event_id: int, user_id: int):
        """Функция состояния нажатия на кнопку "Готов ответить"
        1) Меняет состояние игры
        2) Запоминает id пользователя который будет отвечать
        3)

        :param event_id: id события на которое надо будет послать ответ
        :param user_id: user_id на который будет послан ответ
        :return:
        """
        if (
            self.game_state == GameStage.WAITING_READY_TO_ANSWER
            and user_id in self.players
        ):
            self.game_state = GameStage.WAITING_ANSWER
            self.answered_player_id = user_id
            self.answered_player = await self.vk_accessor.get_vk_user(user_id)

            await self.app.store.game_accessor.change_state(
                game_id=self.game_id, new_state=GameStage.WAITING_ANSWER
            )
            await self.game_accessor.change_answer_player(
                game_id=self.game_id, vk_user_id=user_id
            )
            await self.vk_accessor.send_event_answer(
                event_id=event_id,
                peer_id=self.conversation_id,
                user_id=user_id,
                response_text=f"Поздравляю, ты отвечаешь на вопрос,"
                f"У тебя {self.time_to_answer} секунд!",
            )

            keyboard_start_game = VkKeyboard(one_time=True)
            vk_user = await self.vk_accessor.get_vk_user(user_id)
            await self.vk_accessor.send_message(
                peer_id=self.conversation_id,
                text=f"На вопрос отвечает"
                f" {vk_user.last_name} {vk_user.first_name}!",
                keyboard=await keyboard_start_game.get_keyboard(),
            )

        elif self.game_state == GameStage.WAITING_ANSWER:
            await self.vk_accessor.send_event_answer(
                event_id=event_id,
                peer_id=self.conversation_id,
                user_id=user_id,
                response_text="К сожалению не успел!",
            )

        else:
            await self.vk_accessor.send_event_answer(
                event_id=event_id,
                peer_id=self.conversation_id,
                user_id=user_id,
                response_text="Уже нет в этом смысла!",
            )

    async def waiting_answer(self, user_id, answer):
        """Функция принимает ответ игрока во время ожидания ответа
        1) Проверяет верность ответа
        2) Проверяет есть ли ещё вопросы

        :param user_id: id юзера вк от которого ждем ответ
        :param answer: Приходящее сообщение
        :return:
        """
        if (
            self.game_state == GameStage.WAITING_ANSWER
            and user_id == self.answered_player_id
        ):
            await self.game_accessor.change_answer_player(
                game_id=self.game_id, vk_user_id=None
            )

            if answer in self.answers:
                await self.game_accessor.player_add_answer_from_game(
                    answer_id=self.answers[answer].id,
                    player_id=30,
                    game_id=self.game_id,
                )

                await self.vk_accessor.send_message(
                    peer_id=self.conversation_id,
                    text=f"Игрок: {self.answered_player} ответил правильно"
                    f" и получил {self.answers.pop(answer).score} очков!",
                )

                if len(self.answers.keys()) == 0:
                    self.game_state = GameStage.FINISHED
                    await self.game_accessor.change_state(
                        game_id=self.game_id, new_state=GameStage.FINISHED
                    )
                    await self.end_game()

                else:
                    await self._resend_question()
                    self.game_state = GameStage.WAITING_READY_TO_ANSWER
                    await self.game_accessor.change_state(
                        game_id=self.game_id,
                        new_state=GameStage.WAITING_READY_TO_ANSWER,
                    )

            else:
                self.game_state = GameStage.WAITING_READY_TO_ANSWER
                await self.game_accessor.change_state(
                    game_id=self.game_id,
                    new_state=GameStage.WAITING_READY_TO_ANSWER,
                )
                await self._resend_question()

    async def end_game(self):
        await self.vk_accessor.send_message(
            peer_id=self.conversation_id, text="Игра окончена!"
        )

    async def cancel_game(self):
        await self.game_accessor.change_state(
            game_id=self.game_id, new_state=GameStage.CANCELED
        )

        keyboard_empty = VkKeyboard()
        await self.vk_accessor.send_message(
            peer_id=self.conversation_id,
            text="Игра отменена!",
            keyboard=await keyboard_empty.get_keyboard(),
        )

    def __repr__(self):
        return f"Это игра из {self.conversation_id}"
