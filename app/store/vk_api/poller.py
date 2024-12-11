import asyncio
from asyncio import Future, Task
from logging import getLogger


from app.store import Store


class Poller:
    def __init__(self, store: Store) -> None:
        self.store = store
        self.is_running = False
        self.poll_task: Task | None = None
        self.logger = getLogger("Poller")

    def _done_callback(self, result: Future) -> None:
        if result.exception():
            self.store.bots_manager.logger.exception(
                "poller stopped with exception", exc_info=result.exception()
            )
        if self.is_running:
            self.start()

    def start(self) -> None:
        self.is_running = True

        self.poll_task = asyncio.create_task(self.poll())
        self.poll_task.add_done_callback(self._done_callback)

    async def stop(self) -> None:
        self.is_running = False

        await self.poll_task

    async def poll(self) -> None:
        while self.is_running:
            try:
                await self.store.vk_api.poll()
            except Exception as e:
                self.logger.exception("Poll error, Бот остановлен!", exc_info=e)
                await self.stop()
