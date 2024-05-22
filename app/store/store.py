import typing

from app.store.database.database import Database

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from app.store.admin.accessor import AdminAccessor
        from app.store.game.accessor import GameAccessor, GameSettingsAccessor
        from app.store.game.manager import BotManager
        from app.store.quiz.accessor import QuizAccessor
        from app.store.vk_api.accessor import VkApiAccessor

        self.quizzes = QuizAccessor(app)
        self.admins = AdminAccessor(app)
        self.vk_api = VkApiAccessor(app)

        self.bots_manager = BotManager(app)
        self.game_accessor = GameAccessor(app)
        self.game_settings_accessor = GameSettingsAccessor(app)


def setup_store(app: "Application"):
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.store = Store(app)
