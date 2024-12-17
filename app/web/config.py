import typing
from dataclasses import dataclass

import yaml

if typing.TYPE_CHECKING:
    from app.web.app import Application


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


def setup_config(app: "Application", config_path: str):
    # Сюда добавляются адресы откуда будет идти запрос на api
    # т.е. Адреса с реактом админки
    allowed_origins = [
        "http://0.0.0.0:3000",
        "http://localhost:3000",
    ]
    # добавление адресов с локальной разработкой
    for i in range(10):
        allowed_origins.append(f"http://10.252.1.{i}:3000")
        allowed_origins.append(f"http://10.252.1.{i}:3001")

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
