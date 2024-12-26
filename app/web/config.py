import typing
from dataclasses import dataclass
from logging import getLogger

import yaml
from cryptography.fernet import Fernet

if typing.TYPE_CHECKING:
    from app.web.app import Application

logger = getLogger(__name__)


@dataclass
class SessionConfig:
    key: str | None = None
    cookie_name: str = "session"
    samesite: str = "Lax"
    path: str = "/"
    secure: bool = True


@dataclass
class AdminConfig:
    email: str
    password: str


@dataclass
class BotConfig:
    token: str
    group_id: int
    is_turn_on: bool = True


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    database: str = "project"


@dataclass
class Config:
    admin: AdminConfig
    session: SessionConfig | None = None
    bot: BotConfig | None = None
    database: DatabaseConfig | None = None
    allowed_origins: list[str] | None = None


def setup_config(app: "Application", config_path: str) -> None:
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    session_key = raw_config["session"]["key"]
    if session_key is None:
        session_key = Fernet.generate_key()

    app.config = Config(
        session=SessionConfig(
            key=session_key,
            cookie_name=raw_config["session"]["cookie_name"],
            samesite=raw_config["session"]["samesite"],
            path=raw_config["session"]["path"],
            secure=raw_config["session"]["secure"],
        ),
        admin=AdminConfig(
            email=raw_config["admin"]["email"],
            password=raw_config["admin"]["password"],
        ),
        bot=BotConfig(
            token=raw_config["bot"]["token"],
            group_id=raw_config["bot"]["group_id"],
            is_turn_on=raw_config["bot"]["is_turn_on"],
        ),
        database=DatabaseConfig(**raw_config["database"]),
    )
