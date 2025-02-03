import typing

from app.blitz.views import (
    QuestionAddView,
    QuestionDeleteByIdView,
    QuestionGetByIdView,
    QuestionListView,
    QuestionPatchById,
    ThemeAddView,
    ThemeDeleteByIdView,
    ThemeListView,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/api/v1/game/blitz.themes_add", ThemeAddView)
    app.router.add_view("/api/v1/game/blitz.themes_list", ThemeListView)
    app.router.add_view("/api/v1/game/blitz.themes_delete_by_id", ThemeDeleteByIdView)

    app.router.add_view("/api/v1/game/blitz.questions_add", QuestionAddView)
    app.router.add_view("/api/v1/game/blitz.questions_get_by_id", QuestionGetByIdView)
    app.router.add_view("/api/v1/game/blitz.questions_list", QuestionListView)
    app.router.add_view(
        "/api/v1/game/blitz.questions_delete_by_id", QuestionDeleteByIdView
    )
    app.router.add_view("/api/v1/game/blitz.questions_patch_by_id", QuestionPatchById)
