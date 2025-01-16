import pytest

from app.games.blitz.logic import GameBlitz


class TestBlitzGameSuccess:
    @pytest.mark.parametrize(
        ("conversation_id", "admin_id"),
        [
            (13007796, 13007796),
            ("13007796", "13007796"),
        ],
    )
    async def test_init_game_success(
        self, application, mock_questions, conversation_id, admin_id
    ):
        game_blitz = GameBlitz(
            application,
            conversation_id=conversation_id,
            admin_id=admin_id,
            questions=mock_questions,
        )
        assert game_blitz.admin_id == 13007796
        assert game_blitz.conversation_id == 13007796
        assert game_blitz.questions == mock_questions
