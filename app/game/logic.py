import asyncio
import typing
from logging import getLogger

import sqlalchemy.orm.exc

from app.game.models import Game, GameStage, Player
from app.store.vk_api.dataclasses import VkUser
from app.store.vk_api.utils import VkButton, VkKeyboard

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameLogic:
    def __init__(self, app: "Application", game_model: Game):
        self.game_id = None
        self.app = app
        self.logger = getLogger("BotManager")

        self.players_list = game_model.players  # Список игроков
        self.time_to_answer = 5  # время данное на ответ
        self.question = game_model.question
        self.answers: dict = {}

        for answer in game_model.question.answers:
            self.answers[answer.title.lower()] = answer

        try:
            for _ in game_model.player_answers_games:
                self.answers.pop(_.answer.title.lower())
        except sqlalchemy.orm.exc.DetachedInstanceError:
            pass

        self.time_to_registration = 5
        self.min_count_gamers: int = 1  # ТЕстовые данные
        self.max_count_gamers: int = 5  # Тестовые данные

        self.conversation_id: int = game_model.conversation_id
        self.game_state: GameStage = game_model.state

        self.answered_player: VkUser | None = None
        self.answered_player_id: int | None = game_model.responsed_player_id

        self.players = game_model.players
        self.players: dict = {}

        if game_model.players:
            for player in game_model.players:
                self.players[player.vk_user_id] = player
        self.players_vk_id: list[int] = []

        self.game_id = game_model.id
        self.question_id: game_model.question_id

    async def _registration_timer(self):
        await asyncio.sleep(self.time_to_registration)

        if self.game_state != GameStage.REGISTRATION_GAMERS:
            raise asyncio.CancelledError

        if self.min_count_gamers <= len(self.players) <= self.max_count_gamers:
            self.game_state = GameStage.WAITING_READY_TO_ANSWER
            await self.app.store.game_accessor.change_state(
                game_id=self.game_id,
                new_state=GameStage.WAITING_READY_TO_ANSWER,
            )
            await self.app.store.vk_api.send_message(
                peer_id=self.conversation_id,
                text=f"Время вышло, набралось достаточное количество игроков!\n"
                f"Зарегестрировалось: {len(self.players)}\n"
                f"Минимально необходимо: {self.min_count_gamers}\n",
            )
            await self._resend_question(delay=1)

        else:
            await self.app.store.vk_api.send_message(
                peer_id=self.conversation_id,
                text=f"Время вышло, не набралось достаточное количество игроков!\n"
                f"Зарегестрировалось: {len(self.players)}\n"
                f"Минимально необходимо: {self.min_count_gamers}\n",
            )
            await self.cancel_game()

    async def _resend_question(self, delay: int = 0):
        """
        Отправка вопроса в игру
        :param delay: задержка в секундах на отправку сообщения
        :return:
        """
        await self.app.store.vk_api.send_message(
            peer_id=self.conversation_id, text="Внимание вопрос!"
        )
        await asyncio.sleep(delay)
        keyboard_start_game = VkKeyboard(one_time=False)
        btn_ready_to_answer = VkButton(
            label="Знаю ответ!",
            type_btn="callback",
            payload={"type": "show_snackbar", "text": "/give_answer"},
            color="primary",
        ).get()

        text = f"{self.question.title} \n"

        for k, v in self.answers.items():
            _ = "X" * len(k)
            text += f"{_} = {v.score} очков\n"

        await keyboard_start_game.add_line([btn_ready_to_answer])
        await self.app.store.vk_api.send_message(
            peer_id=self.conversation_id,
            text=text,
            keyboard=await keyboard_start_game.get_keyboard(),
        )

    async def get_state(self):
        await self.app.store.vk_api.send_message(
            peer_id=self.conversation_id,
            text=f"Cейчас идет {self.game_state}",
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

            await self.app.store.vk_api.send_message(
                peer_id=self.conversation_id,
                text="Началась регистрация на игру!",
                keyboard=await keyboard_start_game.get_keyboard(),
            )
            self.game_state = GameStage.REGISTRATION_GAMERS
            await self.app.store.game_accessor.change_state(
                game_id=self.game_id, new_state=GameStage.REGISTRATION_GAMERS
            )

            background_tasks = set()
            task = asyncio.create_task(self._registration_timer())
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)

        else:
            await self.app.store.vk_api.send_message(
                peer_id=self.conversation_id,
                text="Невозможно сейчас начать игру, т.к. она уже идет",
            )

    async def register_player(self, event_id, user_id):
        if self.game_state == GameStage.REGISTRATION_GAMERS:
            self.logger.info("Регистрируем игрока")

            if user_id not in self.players:
                player: Player = await (
                    self.app.store.game_accessor.get_player_by_vk_id_game_id(
                        user_id, self.game_id
                    )
                )

                if player is None:
                    vk_user = await self.app.store.vk_api.get_vk_user(user_id)
                    await self.app.store.game_accessor.add_player(
                        game_id=self.game_id,
                        vk_user_id=vk_user.id,
                        name=f"{vk_user.last_name} {vk_user.first_name}",
                    )
                else:
                    await self.app.store.game_accessor.add_player(
                        game_id=self.game_id,
                        vk_user_id=user_id,
                        name=f"{player.name}",
                    )
                self.players[user_id] = player

                if len(self.players) >= self.max_count_gamers:
                    self.game_state = GameStage.WAITING_READY_TO_ANSWER
                    await self.app.store.game_accessor.change_state(
                        game_id=self.game_id,
                        new_state=GameStage.WAITING_READY_TO_ANSWER,
                    )

                    await self.app.store.vk_api.send_message(
                        peer_id=self.conversation_id,
                        text=f"Набралось достаточное количество игроков"
                    )
                    await self._resend_question()

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
        if self.game_state == GameStage.REGISTRATION_GAMERS:
            if user_id in self.players:
                self.players.pop(user_id)
                await self.app.store.game_accessor.delete_player(
                    game_id=self.game_id, vk_user_id=user_id
                )

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
            self.answered_player = await self.app.store.vk_api.get_vk_user(
                user_id
            )

            await self.app.store.game_accessor.change_state(
                game_id=self.game_id, new_state=GameStage.WAITING_ANSWER
            )
            await self.app.store.game_accessor.change_answer_player(
                game_id=self.game_id, vk_user_id=user_id
            )
            await self.app.store.vk_api.send_event_answer(
                event_id=event_id,
                peer_id=self.conversation_id,
                user_id=user_id,
                response_text=f"Поздравляю, ты отвечаешь на вопрос,"
                f"У тебя {self.time_to_answer} секунд!",
            )

            keyboard_start_game = VkKeyboard(one_time=True)
            vk_user = await self.app.store.vk_api.get_vk_user(user_id)
            await self.app.store.vk_api.send_message(
                peer_id=self.conversation_id,
                text=f"На вопрос отвечает"
                f" {vk_user.last_name} {vk_user.first_name}!",
                keyboard=await keyboard_start_game.get_keyboard(),
            )

        elif self.game_state == GameStage.WAITING_ANSWER:
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

    async def waiting_answer(self, user_id: int, answer: str):
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
            await self.app.store.game_accessor.change_answer_player(
                game_id=self.game_id, vk_user_id=None
            )

            if answer.lower() in self.answers:
                player: Player = await (
                    self.app.store.game_accessor.get_player_by_vk_id_game_id(
                        vk_id=user_id, game_id=self.game_id
                    )
                )
                await self.app.store.game_accessor.player_add_answer_from_game(
                    answer_id=self.answers[answer.lower()].id,
                    player_id=player.id,
                    game_id=self.game_id,
                )

                await self.app.store.vk_api.send_message(
                    peer_id=self.conversation_id,
                    text=f"Игрок: {self.answered_player} ответил правильно! \n"
                    f" Получил {self.answers.pop(answer.lower()).score}"
                    f" очков!",
                )

                if len(self.answers.keys()) == 0:
                    self.game_state = GameStage.FINISHED
                    await self.app.store.game_accessor.change_state(
                        game_id=self.game_id, new_state=GameStage.FINISHED
                    )
                    await self.end_game()

                else:
                    await self._resend_question()
                    self.game_state = GameStage.WAITING_READY_TO_ANSWER
                    await self.app.store.game_accessor.change_state(
                        game_id=self.game_id,
                        new_state=GameStage.WAITING_READY_TO_ANSWER,
                    )

            else:
                self.game_state = GameStage.WAITING_READY_TO_ANSWER
                await self.app.store.game_accessor.change_state(
                    game_id=self.game_id,
                    new_state=GameStage.WAITING_READY_TO_ANSWER,
                )
                await self._resend_question()

    async def end_game(self):
        text = "Игра окончена, таблица победитей:\n\n"
        players_scores = await self.app.store.game_accessor.get_score(
            game_id=self.game_id
        )

        for player_name, player_score in players_scores:
            text += "   {:<15} :{:<5} очков\n".format(player_name, player_score)

        text += "\n\n Всем спасибо за игру!"
        await self.app.store.vk_api.send_message(
            peer_id=self.conversation_id, text=text
        )

    async def cancel_game(self):
        self.game_state = GameStage.CANCELED
        await self.app.store.game_accessor.change_state(
            game_id=self.game_id, new_state=GameStage.CANCELED
        )
        keyboard_empty = VkKeyboard()
        await self.app.store.vk_api.send_message(
            peer_id=self.conversation_id,
            text="Игра отменена!",
            keyboard=await keyboard_empty.get_keyboard(),
        )

    def __repr__(self):
        return f"Это игра из {self.conversation_id}"
