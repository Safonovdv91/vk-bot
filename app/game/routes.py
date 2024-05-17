import typing

from app.game.views import (
    GameGetByIdView,
    GameListView,
    GameProfileListActiveView,
    SettingsAddView,
    SettingsGetByIdView,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/game.list_active", GameProfileListActiveView)
    app.router.add_view("/game.list", GameListView)
    app.router.add_view("/game.get_by_id", GameGetByIdView)

    app.router.add_view("/game/profile.get_by_id", SettingsGetByIdView)
    app.router.add_view("/game/profile.add", SettingsAddView)
