import random
import typing
from urllib.parse import urlencode, urljoin

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.vk_api.dataclasses import (
    LongPollResponse,
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
                await self.app.store.bots_manager.handle_updates(messages)

            except Exception:
                self.logger.exception(
                    "Не вышло переслать сообщения в Bot Manager"
                )

    async def send_personal_message(self, message: SendMessage) -> None:
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
