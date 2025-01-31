import typing

from app.games.blitz.views import (
    BlitzGameActiveListView,
    BlitzGameChangeStatusView,
    BlitzGameListView,
    BlitzGameStartView,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/api/game/blitz.start_game", BlitzGameStartView)
    app.router.add_view("/api/game/blitz.change_game_stage", BlitzGameChangeStatusView)
    app.router.add_view("/api/game/blitz.get_game", BlitzGameListView)
    app.router.add_view("/api/game/blitz.get_active_games", BlitzGameActiveListView)
