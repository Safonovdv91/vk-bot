import typing
from dataclasses import dataclass
from logging import getLogger
from os import getenv

import yaml

if typing.TYPE_CHECKING:
    from app.web.app import Application

logger = getLogger(__name__)


@dataclass
class SessionConfig:
    key: str


@dataclass
class AdminConfig:
    email: str
    password: str


@dataclass
class BotConfig:
    token: str
    group_id: int


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
    if getenv("STATUS") == "DEV":
        logger.info("Dev mode activated")
        allowed_origins = [
            "http://0.0.0.0:3000",
            "http://localhost:3000",
            "http://localhost:3001",
        ]
        # добавление адресов с локальной разработкой
        for i in range(10):
            allowed_origins.append(f"http://10.252.1.{i}:3000")
            allowed_origins.append(f"http://10.252.1.{i}:3001")

        logger.info("Allowed origins: %s", allowed_origins)

        app.config = Config(
            session=SessionConfig(
                key="-6b97CSkbEPmpKWCBixxy9yER2IXEyoO19XFj420dKs=",
            ),
            admin=AdminConfig(
                email="admin@admin.com",
                password="admin",
            ),
            bot=BotConfig(
                token="vk1.a.XIDKJZTUyQ24nViGDAYxN78v2VvAXtu1In2ra9rI9i9Gx6L0KoKS2GFcrjFTfpr71wvatzW9N8_LMwpuZxU5Gi-TYMxE6ybdIZ4NBZeUYRFntpiKUvHPDwVmx4QTCWCAN9rEuVJwhzKAh8BbYM6xZf6hdLoi5nyY5WBoaeaXsd6yfWFZKpzBi5N6zIfmAYFUoTNgjvgRc-hQbTovpHBI6A",
                group_id=218897004,
            ),
            database=DatabaseConfig(
                host=getenv("DB_HOST"),
                port=int(getenv("DB_PORT")),
                user=getenv("DB_USER"),
                password=getenv("DB_PASSWORD"),
                database=getenv("DB_NAME"),
            ),
            allowed_origins=allowed_origins,
        )
    else:
        with open(config_path, "r") as f:
            raw_config = yaml.safe_load(f)

        app.config = Config(
            session=SessionConfig(
                key=raw_config["session"]["key"],
            ),
            admin=AdminConfig(
                email=raw_config["admin"]["email"],
                password=raw_config["admin"]["password"],
            ),
            bot=BotConfig(
                token=raw_config["bot"]["token"],
                group_id=raw_config["bot"]["group_id"],
            ),
            database=DatabaseConfig(**raw_config["database"]),
            allowed_origins=allowed_origins,
        )
