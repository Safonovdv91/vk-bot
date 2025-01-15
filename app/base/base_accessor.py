import typing
from logging import getLogger

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BaseAccessor:
    def __init__(self, app: "Application", *args, **kwargs):
        self.app = app
        self.logger = getLogger(__name__)

        app.on_startup.append(self.connect)
        app.on_cleanup.append(self.disconnect)

    async def connect(self, app: "Application"):
        self.logger.info("Connected to database")
        return

    async def disconnect(self, app: "Application"):
        self.logger.info("Disconnected from database")
        return
