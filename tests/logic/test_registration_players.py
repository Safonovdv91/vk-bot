from app.games.game_100.constants import GameStage


def test_something_with_game(mock_game):
    assert mock_game.state == GameStage.REGISTRATION_GAMERS
