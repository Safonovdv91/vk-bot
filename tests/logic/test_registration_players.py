from app.game.constants import GameStage


def test_something_with_game(mock_game):
    assert mock_game.state == GameStage.REGISTRATION_GAMERS
