import typing

from app.quiz.views import (
    QuestionAddView,
    QuestionDeleteByIdView,
    QuestionGetByIdView,
    QuestionGetCountByThemeId,
    QuestionListView,
    QuestionPatchById,
    ThemeAddView,
    ThemeDeleteByIdView,
    ThemeListView,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/api/v1/game/quiz.themes_add", ThemeAddView)
    app.router.add_view("/api/v1/game/quiz.themes_list", ThemeListView)
    app.router.add_view("/api/v1/game/quiz.themes_delete_by_id", ThemeDeleteByIdView)

    app.router.add_view("/api/v1/game/quiz.questions_add", QuestionAddView)
    app.router.add_view("/api/v1/game/quiz.questions_get_by_id", QuestionGetByIdView)
    app.router.add_view("/api/v1/game/quiz.questions_list", QuestionListView)
    app.router.add_view("/api/v1/game/quiz.questions_count", QuestionGetCountByThemeId)
    app.router.add_view(
        "/api/v1/game/quiz.questions_delete_by_id", QuestionDeleteByIdView
    )
    app.router.add_view("/api/v1/game/quiz.questions_patch_by_id", QuestionPatchById)
