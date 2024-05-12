import json
import random
import typing
from logging import getLogger
from urllib.parse import urlencode, urljoin

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.vk_api.constants import (
    API_PATH,
    API_VERSION,
    VK_METHOD_ACT,
    VK_METHOD_WAIT,
    VkMessagesMethods,
)
from app.store.vk_api.dataclasses import (
    LongPollResponse,
    VkUser,
)
from app.store.vk_api.poller import Poller

if typing.TYPE_CHECKING:
    from app.web.app import Application


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)

        self._API_PATH: str = API_PATH
        self._API_VERSION: str = API_VERSION
        self._VK_METHOD_ACT: str = VK_METHOD_ACT
        self._VK_METHOD_WAIT: int = kwargs.get("wait", VK_METHOD_WAIT)

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

    async def _send_request(
        self, method: VkMessagesMethods, params: dict
    ) -> dict | None:
        """Отправка запроса к API Вконтакте"""
        params["access_token"] = self.app.config.bot.token

        try:
            async with self.session.post(
                self._build_query(self._API_PATH, method.value, params)
            ) as response:
                return await response.json()

        except Exception as e:
            self.logger.error("Ошибка при отправке запроcа в VkApi", exc_info=e)

            return None

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
            messages, events = [], []

            for update in long_poll_response.updates:
                if update.type == "message_new":
                    messages.append(update)
                elif update.type == "message_event":
                    events.append(update)

            try:
                await self.app.store.bots_manager.handle_events(events)
                await self.app.store.bots_manager.handle_updates(messages)

            except Exception as e:
                self.logger.exception(
                    "Не вышло переслать сообщения в Bot Manager", exc_info=e
                )

    async def send_message(
        self, peer_id: int, text: str, keyboard: str | None = None
    ) -> None:
        """Выслать сообщение
        :param keyboard: Строкове представление клавиатуры
        :param text: Текст сообщения
        :param peer_id: id беседы в которую отправить сообщение
        :return:
        """
        params = {
            "random_id": random.randint(1, 2**32),
            "peer_id": peer_id,
            "message": text,
        }

        if keyboard:
            params["keyboard"] = keyboard

        await self._send_request(VkMessagesMethods.send, params)

    async def get_vk_user(self, user_id):
        params = {
            "user_ids": user_id,
        }
        data = await self._send_request(VkMessagesMethods.get, params)
        response = data.get("response")

        if response:
            return VkUser(
                id=response[0].get("id"),
                first_name=response[0].get("first_name"),
                last_name=response[0].get("last_name"),
            )
        return None

    async def edit_message(
        self, peer_id: int, conversation_message_id, text: str
    ) -> None:
        """Редактирует сообщение в беседе
        :param text: Новый текст сообщения
        :param peer_id: id беседы в которую отправить сообщение
        :param conversation_message_id: id сообщения которое необходимо поменять
        """
        params = {
            "random_id": random.randint(1, 2**32),
            "peer_id": peer_id,
            "conversation_message_id": conversation_message_id,
            "message": text,
        }
        await self._send_request(VkMessagesMethods.edit, params)

    async def pin_message(self, peer_id: int, message_id: int) -> None:
        """Закрепляет сообщение
        :param peer_id: Идентификатор диалога, в котором нажата кнопка.
        :param message_id: Идентификатор сообщения которое надо запинить.
        :return:
        """
        params = {
            "peer_id": peer_id,
            "conversation_message_id": message_id,
        }
        await self._send_request(VkMessagesMethods.pin, params)

    async def unpin_message(self, peer_id: int) -> None:
        """Открепляет закрепленное сообщение
        :param peer_id: Идентификатор диалога, в котором нажата кнопка.
        """
        params = {
            "random_id": random.randint(1, 2**32),
            "peer_id": peer_id,
        }
        await self._send_request(VkMessagesMethods.unpin, params)

    async def send_event_answer(
        self, event_id, user_id, response_text, peer_id: int
    ) -> None:
        """Отправляет ответ на событие нажатия callback-кнопки.
        :param event_id: id события нажатия на кнопку.
        :param user_id: id пользователя, нажавшего на кнопку.
        :param peer_id: id диалога, в котором нажата кнопка.
        :param response_text: Текст ответа, который будет всплывет.
        """
        event_data = json.dumps(
            {"type": "show_snackbar", "text": response_text}
        )
        params = {
            "event_id": event_id,
            "event_data": event_data,
            "user_id": user_id,
            "peer_id": peer_id,
        }
        await self._send_request(VkMessagesMethods.send_event_answer, params)
