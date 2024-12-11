import asyncio
import typing
from logging import getLogger

import sqlalchemy.orm.exc

from app.game.constants import GameStage
from app.game.models import Game, Player
from app.store.vk_api.dataclasses import VkUser
from app.store.vk_api.utils import VkButton, VkKeyboard

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameLogic:
    def __init__(
        self,
        app: "Application",
        game_model: Game,
    ):
        self.game_id = None
        self.app = app
        self.logger = getLogger("BotManager")
        self.background_tasks = set()
        self.game_model = game_model
        self.pinned_message_id = self.game_model.pinned_conversation_message_id
        self.game_id = game_model.id
        self.question_id: game_model.question_id
        self.players_list = game_model.players  # Список игроков
        self.question = game_model.question
        self.time_to_registration: int = game_model.profile.time_to_registration
        self.time_to_answer: int = game_model.profile.time_to_answer
        self.min_count_gamers: int = game_model.profile.min_count_gamers
        self.max_count_gamers: int = game_model.profile.max_count_gamers
        self.conversation_id: int = game_model.conversation_id
        self.game_state: GameStage = game_model.state
        self.answers: dict = {}

        for answer in game_model.question.answers:
            self.answers[answer.title.lower()] = answer

        try:
            for _ in game_model.player_answers_games:
                self.answers.pop(_.answer.title.lower())
        except sqlalchemy.orm.exc.DetachedInstanceError:
            pass

        self.answered_player: VkUser = VkUser(id=1, first_name="", last_name="")
        self.answered_player_id: int | None = game_model.responsed_player_id

        self.players: dict = {}

        if game_model.players:
            for player in game_model.players:
                self.players[player.vk_user_id] = player
        self.players_vk_id: list[int] = []

    async def _answer_timer(self):
        try:
            await asyncio.sleep(self.time_to_answer)

            self.game_state = GameStage.WAITING_READY_TO_ANSWER
            await self.app.store.game_accessor.change_state(
                game_id=self.game_id,
                new_state=GameStage.WAITING_READY_TO_ANSWER,
            )
            await self.app.store.vk_api.send_message(
                peer_id=self.conversation_id,
                text="Время вышло,игрок не успел ответить",
            )
            await self._resend_question(delay=1)
        except asyncio.CancelledError:
            pass

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
                text=f"Время вышло, не набралось достаточное"
                f" количество игроков!\n"
                f"Зарегестрировалось: {len(self.players)}\n"
                f"Минимально необходимо: {self.min_count_gamers}\n",
            )
            await self.cancel_game(self.game_model.admin_game_id)

    async def _resend_question(self, delay: int = 0):
        """Отправка вопроса в игру
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
        await keyboard_start_game.add_line([btn_ready_to_answer])
        await self.app.store.vk_api.send_message(
            peer_id=self.conversation_id,
            text=text,
            keyboard=await keyboard_start_game.get_keyboard(),
        )
        await self._send_answers_list()

    async def _send_answers_list(self, is_close_answers: bool = True):
        text = "________ \n"

        if is_close_answers:
            for answer in self.game_model.question.answers:
                if answer.title.lower() not in self.answers:
                    text += f"| {answer.title} | = {answer.score} очков\n"
                else:
                    _ = "X" * len(answer.title)
                    text += (
                        f"| {_} | ({len(answer.title)})  "
                        f"= {answer.score} очков\n"
                    )

        else:
            for answer in self.game_model.question.answers:
                text += f"| {answer.title} | = {answer.score} очков\n"

        text += "________ \n"
        await self.app.store.vk_api.send_message(
            peer_id=self.conversation_id,
            text=text,
        )

    async def start_game(self, admin_id: int):
        if self.game_state == GameStage.WAIT_INIT:
            self.game_model.admin_game_id = admin_id
            await self.app.store.game_accessor.change_admin_game_id(
                game_id=self.game_id, vk_user_id=admin_id
            )
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
                text=f"Началась регистрация на игру!\n"
                f" Режим игры :\n{self.game_model.profile}\n",
                keyboard=await keyboard_start_game.get_keyboard(),
            )

            self.pinned_message_id = await self.app.store.vk_api.send_message(
                peer_id=self.conversation_id,
                text="Зарегистриованные игроки:",
            )
            await self.app.store.game_accessor.change_pinned_message(
                game_id=self.game_id, id_pinned_message=self.pinned_message_id
            )
            await self.app.store.vk_api.pin_message(
                peer_id=self.conversation_id, message_id=self.pinned_message_id
            )
            self.game_state = GameStage.REGISTRATION_GAMERS
            await self.app.store.game_accessor.change_state(
                game_id=self.game_id, new_state=GameStage.REGISTRATION_GAMERS
            )

            task = asyncio.create_task(self._registration_timer())
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)

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
                    player: VkUser = await self.app.store.vk_api.get_vk_user(
                        user_id
                    )
                    await self.app.store.game_accessor.add_player(
                        game_id=self.game_id,
                        vk_user_id=player.id,
                        name=f"{player.last_name} {player.first_name}",
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
                        text="Набралось достаточное " "количество игроков",
                    )
                    await self._resend_question()

                await self.app.store.vk_api.send_event_answer(
                    event_id=event_id,
                    peer_id=self.conversation_id,
                    user_id=user_id,
                    response_text="Успешная регистрация!",
                )
                pinned_text = (
                    f"Игроки: ({len(self.players)}/{self.max_count_gamers})\n"
                )

                for v in self.players.values():
                    pinned_text += f"-- {v.last_name} {v.first_name} \n"

                await self.app.store.vk_api.edit_message(
                    peer_id=self.conversation_id,
                    conversation_message_id=self.pinned_message_id,
                    text=pinned_text,
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
                pinned_text = (
                    f"Игроки: ({len(self.players)}/{self.max_count_gamers})\n"
                )

                for v in self.players.values():
                    pinned_text += f"-- {v.last_name} {v.first_name} \n"

                await self.app.store.vk_api.edit_message(
                    peer_id=self.conversation_id,
                    conversation_message_id=self.pinned_message_id,
                    text=pinned_text,
                )

            else:
                await self.app.store.vk_api.send_event_answer(
                    event_id=event_id,
                    peer_id=self.conversation_id,
                    user_id=user_id,
                    response_text="Вы не зарегестрированы!",
                )

        else:
            await self.app.store.vk_api.send_event_answer(
                event_id=event_id,
                peer_id=self.conversation_id,
                user_id=user_id,
                response_text="Играть могут только зарегестрированные игрроки",
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
                response_text="Поздравляю, ты отвечаешь на вопрос!",
            )

            keyboard_start_game = VkKeyboard(one_time=True)
            vk_user = await self.app.store.vk_api.get_vk_user(user_id)
            await self.app.store.vk_api.send_message(
                peer_id=self.conversation_id,
                text=f"На вопрос отвечает"
                f" {vk_user.last_name} {vk_user.first_name}!",
                keyboard=await keyboard_start_game.get_keyboard(),
            )

            task = asyncio.create_task(self._answer_timer())
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)

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
            for task in self.background_tasks:
                task.cancel()

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
                if self.answered_player is None:
                    self.answered_player = ""

                await self.app.store.vk_api.send_message(
                    peer_id=self.conversation_id,
                    text=f"Игрок: {self.answered_player} ответил правильно! \n"
                    f" Получил {self.answers.pop(answer.lower()).score}"
                    f" очков! \n",
                )

                if len(self.answers.keys()) == 0:
                    await self.end_game(user_id=user_id)

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

    async def end_game(self, user_id: int) -> bool:
        if user_id in self.players or user_id == self.game_model.admin_game_id:
            self.game_state = GameStage.FINISHED
            await self.app.store.game_accessor.change_state(
                game_id=self.game_id, new_state=GameStage.FINISHED
            )
            await self.app.store.vk_api.send_message(
                peer_id=self.conversation_id,
                text="Игра окончена!",
                keyboard=await VkKeyboard().get_keyboard(),
            )
            players_scores = await self.app.store.game_accessor.get_score(
                game_id=self.game_id
            )
            text = "Таблица победитей: \n 🏆"

            for player_name, player_score in players_scores:
                text += " {:<15} :{:<5} очков\n".format(
                    player_name, player_score
                )

            text += "\n\n Всем спасибо за игру!"
            await self.app.store.vk_api.send_message(
                peer_id=self.conversation_id,
                text=text,
                keyboard=await VkKeyboard().get_keyboard(),
            )
            await self.app.store.vk_api.unpin_message(
                peer_id=self.conversation_id
            )

            return True

        return False

    async def cancel_game(self, user_id: int) -> bool:
        if user_id == self.game_model.admin_game_id:
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
            await self.app.store.vk_api.unpin_message(
                peer_id=self.conversation_id
            )
            return True

        return False
