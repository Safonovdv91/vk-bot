import json
import random
import typing
from logging import getLogger
from urllib.parse import urlencode, urljoin

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.vk_api.dataclasses import (
    LongPollResponse,
    SendEditMessage,
    SendMessage,
    SendMessageWithKeyboard,
)
from app.store.vk_api.poller import Poller

if typing.TYPE_CHECKING:
    from app.web.app import Application


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)

        self._API_PATH: str = "https://api.vk.com/method/"
        self._API_VERSION: str = "5.131"
        self._VK_METHOD_ACT: str = (
            "a_check"  # Константа от ВК API. Для получения новых событий из ВКю
        )
        self._VK_METHOD_WAIT: int = kwargs.get("wait", 25)

        self.session: ClientSession | None = None
        self.key: str | None = None
        self.server: str | None = None
        self.poller: Poller | None = None
        self.ts: int | None = None
        self.logger = getLogger("VkApiAccessor")

    async def connect(self, app: "Application") -> None:
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))

        try:
            await self._get_long_poll_service()
        except Exception as e:
            self.logger.error("Exception", exc_info=e)

        self.poller = Poller(app.store)
        self.logger.info("start polling")
        self.poller.start()

    async def disconnect(self, app: "Application") -> None:
        if self.session:
            await self.session.close()

        if self.poller:
            self.logger.info("Останавливаем poller")
            await self.poller.stop()

    def _build_query(self, host: str, method: str, params: dict) -> str:
        params.setdefault("v", self._API_VERSION)
        return f"{urljoin(host, method)}?{urlencode(params)}"

    async def _get_long_poll_service(self) -> None:
        async with self.session.get(
            self._build_query(
                host=self._API_PATH,
                method="groups.getLongPollServer",
                params={
                    "group_id": self.app.config.bot.group_id,
                    "access_token": self.app.config.bot.token,
                },
            )
        ) as response:
            data = (await response.json())["response"]
            self.key = data["key"]
            self.server = data["server"]
            self.ts = data["ts"]

    async def poll(self):
        async with self.session.get(
            self._build_query(
                host=self.server,
                method="",
                params={
                    "act": self._VK_METHOD_ACT,
                    "key": self.key,
                    "ts": self.ts,
                    "wait": self._VK_METHOD_WAIT,
                },
            )
        ) as response:
            data = await response.json()
            if data.get("ts") is not None:
                self.ts = data.get("ts")

            long_poll_response: LongPollResponse = (
                LongPollResponse.Schema().load(data)
            )
            self.logger.info("lpresponse \n   %s", long_poll_response)
            try:
                messages = [
                    update
                    for update in long_poll_response.updates
                    if update.type == "message_new"
                ]
                events = [
                    event
                    for event in long_poll_response.updates
                    if event.type == "message_event"
                ]
                await self.app.store.bots_manager.handle_events(events)
                await self.app.store.bots_manager.handle_updates(messages)

            except Exception:
                self.logger.exception(
                    "Не вышло переслать сообщения в Bot Manager"
                )

    async def send_message(self, message: SendMessage) -> None:
        """Выслать простое текстовое сообщение
        :param message: Сообщение котороые необходимо выслать.
        :return:
        """
        async with self.session.post(
            self._build_query(
                self._API_PATH,
                "messages.send",
                params={
                    "access_token": self.app.config.bot.token,
                    "random_id": random.randint(1, 2**32),
                    "peer_id": message.peer_id,
                    "message": message.text.upper(),
                },
            )
        ) as response:
            data = await response.json()
            self.logger.info(data)

    async def send_message_with_keyboard(
        self, message: SendMessageWithKeyboard
    ) -> None:
        """Послать сообщение с клавиатурой
        :param message: Сообщение которое необходимо выслать с клавиатурой.
        :return:
        """
        self.logger.info("Высылаем сообщение с клавиатурой")
        async with self.session.post(
            self._build_query(
                self._API_PATH,
                "messages.send",
                params={
                    "random_id": random.randint(1, 2**32),
                    "peer_id": message.peer_id,
                    "message": message.text,
                    "keyboard": message.keyboard,
                    "access_token": self.app.config.bot.token,
                },
            )
        ) as response:
            data = await response.json()
            self.logger.info(data)

    async def edit_message(self, message: SendEditMessage) -> None:
        """Редактирует сообщение в беседе
        :param message: сообщение которое необходимо отредактировать.
        """
        self.logger.info("Заменяем сообщение")
        async with self.session.post(
            self._build_query(
                self._API_PATH,
                "messages.edit",
                params={
                    "random_id": random.randint(1, 2**32),
                    "peer_id": message.peer_id,
                    "conversation_message_id": message.message_id,
                    "message": message.text,
                    "access_token": self.app.config.bot.token,
                },
            )
        ) as response:
            data = await response.json()
            self.logger.info(data)

    async def pin_message(self, peer_id: int, message_id: int) -> None:
        """Закрепляет сообщение
        :param peer_id: Идентификатор диалога, в котором нажата кнопка.
        :param message_id: Идентификатор сообщения которое надо запинить.
        :return:
        """
        self.logger.info("Закрепляем сообщение")
        async with self.session.post(
            self._build_query(
                self._API_PATH,
                "messages.pin",
                params={
                    "peer_id": peer_id,
                    "conversation_message_id": message_id,
                    "access_token": self.app.config.bot.token,
                },
            )
        ) as response:
            data = await response.json()
            self.logger.info(data)

    async def unpin_message(self, peer_id: int) -> None:
        """Открепляет закрепленное сообщение
        :param peer_id: Идентификатор диалога, в котором нажата кнопка.
        """
        self.logger.info("Открепляем сообщение")
        async with self.session.post(
            self._build_query(
                self._API_PATH,
                "messages.unpin",
                params={
                    "random_id": random.randint(1, 2**32),
                    "peer_id": peer_id,
                    "access_token": self.app.config.bot.token,
                },
            )
        ) as response:
            data = await response.json()
            self.logger.info(data)

    async def send_event_answer(
        self, event_id, user_id, response_text, peer_id: int
    ) -> None:
        """Отправляет ответ на событие нажатия callback-кнопки.
        :param event_id: id события нажатия на кнопку.
        :param user_id: id пользователя, нажавшего на кнопку.
        :param peer_id: id диалога, в котором нажата кнопка.
        :param response_text: Текст ответа, который будет всплывет.
        """
        self.logger.info("Обрабатываем нажатие на callback")
        async with self.session.post(
            self._build_query(
                self._API_PATH,
                "messages.sendMessageEventAnswer",
                params={
                    "event_id": event_id,
                    "event_data": json.dumps(
                        {"type": "show_snackbar", "text": response_text}
                    ),
                    "user_id": user_id,
                    "peer_id": peer_id,
                    "access_token": self.app.config.bot.token,
                },
            )
        ) as response:
            data = await response.json()
            self.logger.info(data)
