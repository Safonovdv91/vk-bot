import typing

from app.game.views import GameGetByIdView, GameProfileListActiveView

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/game.list_active", GameProfileListActiveView)
    app.router.add_view("/game.get_by_id", GameGetByIdView)
