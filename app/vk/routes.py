import typing

from app.vk.views import MessagesListView

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/vk/messages_list", MessagesListView)
