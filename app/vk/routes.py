import typing

from app.vk.views import ConversationsListView, MessagesListView

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/api/v1/vk/messages_list", MessagesListView)
    app.router.add_view("/api/v1/vk/conversations_list", ConversationsListView)
