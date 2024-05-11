import typing

from app.quiz.views import (
    QuestionAddView,
    QuestionDeleteByIdView,
    QuestionListView,
    ThemeAddView,
    ThemeListView,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/quiz.themes_add", ThemeAddView)
    app.router.add_view("/quiz.themes_list", ThemeListView)
    app.router.add_view("/quiz.questions_add", QuestionAddView)
    app.router.add_view("/quiz.questions_list", QuestionListView)
    app.router.add_view("/quiz.questions_delete_by_id", QuestionDeleteByIdView)
