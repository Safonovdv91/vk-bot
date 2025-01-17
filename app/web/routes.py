from aiohttp.web_app import Application


def setup_routes(app: Application):
    from app.admin.routes import setup_routes as admin_setup_routes
    from app.blitz.routes import setup_routes as blitz_setup_routes
    from app.games.game_100.routes import setup_routes as game_setup_routes
    from app.quiz.routes import setup_routes as quiz_setup_routes
    from app.vk.routes import setup_routes as vk_setup_routes

    admin_setup_routes(app)
    quiz_setup_routes(app)
    blitz_setup_routes(app)
    game_setup_routes(app)
    vk_setup_routes(app)
