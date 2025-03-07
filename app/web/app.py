import logging

from aiohttp.web import (
    Application as AiohttpApplication,
    Request as AiohttpRequest,
    View as AiohttpView,
)
from aiohttp_apispec import setup_aiohttp_apispec
from aiohttp_session import setup as session_setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from app.admin.models import AdminModel
from app.logger.logger import setup_logging
from app.store import Store
from app.store.database.database import Database
from app.store.store import setup_store
from app.web.config import Config, setup_config
from app.web.mw import setup_middlewares
from app.web.routes import setup_routes


class Application(AiohttpApplication):
    config: Config | None = None
    store: Store | None = None
    database: Database | None = None


class Request(AiohttpRequest):
    admin: AdminModel | None = None

    @property
    def app(self) -> Application:
        return super().app()


class View(AiohttpView):
    @property
    def request(self) -> Request:
        return super().request

    @property
    def database(self) -> Database:
        return self.request.app.database

    @property
    def store(self) -> Store:
        return self.request.app.store

    @property
    def data(self) -> dict:
        return self.request.get("data", {})


app = Application()


def setup_app(config_path: str) -> Application:
    setup_logging(app, sh_logging_level=logging.DEBUG, fh_logging_level=logging.WARNING)
    setup_config(app, config_path)
    session_setup(
        app,
        EncryptedCookieStorage(
            app.config.session.key,
            cookie_name=app.config.session.cookie_name,
            samesite=app.config.session.samesite,
            path=app.config.session.path,
            secure=app.config.session.secure,
        ),
    )
    setup_routes(app)
    setup_aiohttp_apispec(app, title="Vk Bot", url="/docs/json", swagger_path="/docs")
    setup_middlewares(app)
    setup_store(app)
    return app
