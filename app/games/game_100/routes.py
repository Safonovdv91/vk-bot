import typing

from app.games.game_100.views import (
    AddSettingsView,
    DefaultSettingsView,
    GameGetByIdView,
    GameListView,
    GameProfileListActiveView,
    PatchSettingsView,
    SettingsGetByIdView,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/api/game/list_active", GameProfileListActiveView)
    app.router.add_view("/api/game/list", GameListView)
    app.router.add_view("/api/game/get_by_id", GameGetByIdView)

    app.router.add_view("/api/game/profile.get_by_id", SettingsGetByIdView)
    app.router.add_view("/api/game/profile.patch", PatchSettingsView)
    app.router.add_view("/api/game/profile.add", AddSettingsView)
    app.router.add_view("/api/game/profile_default.patch", DefaultSettingsView)
