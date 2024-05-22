import pytest

from app.game.constants import GameStage
from app.game.models import Game, Player


# Фикстура создаёт мок-экземпляр модели Game
@pytest.fixture
def mock_game(mocker):
    # Создание поддельного экземпляра модели Game с использованием mocker
    mock_game_instance = mocker.Mock(spec=Game)

    # Задание атрибутов для mock экземпляра
    mock_game_instance.id = 1
    mock_game_instance.conversation_id = 111
    mock_game_instance.admin_game_id = 777
    mock_game_instance.responsed_player_id = 666
    mock_game_instance.question_id = 2
    mock_game_instance.state = GameStage.REGISTRATION_GAMERS
    mock_game_instance.profile_id = 1

    # Возвращение мок-экземпляра для использования в тестах
    return mock_game_instance


@pytest.fixture
def mock_player(mocker, game1):
    # Создание поддельного экземпляра модели Game с использованием mocker
    mock_player = mocker.Mock(spec=Player)

    # Задание атрибутов для mock экземпляра
    mock_player.id = 1
    mock_player.vk_user_id = 13007796
    mock_player.name = "Tester_name"
    mock_player.game_id = game1.id

    # Возвращение мок-экземпляра для использования в тестах
    return mock_player
