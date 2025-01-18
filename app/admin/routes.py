import typing

from app.admin.views import AdminCurrentView, AdminLogoutView

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    from app.admin.views import AdminLoginView

    app.router.add_view("/api/admin.login", AdminLoginView)
    app.router.add_view("/api/admin.current", AdminCurrentView)
    app.router.add_view("/api/admin.logout", AdminLogoutView)
