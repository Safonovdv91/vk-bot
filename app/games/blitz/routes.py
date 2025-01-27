from app.games.blitz.views import BlitzGameStartView


def setup_routes(app: "Application"):
    app.router.add_view("/api/game/blitz.start_game", BlitzGameStartView)
