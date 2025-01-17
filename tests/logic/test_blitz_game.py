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


class TestBlitzGameBadData:
    @pytest.mark.parametrize(
        ("conversation_id", "admin_id", "text_error"),
        [
            (-2341, 1241251, "conversation_id должен быть > 0"),
            ("-2341", "1241251", "conversation_id должен быть > 0"),
            ("asdqw", "1241251", "conversation_id должен быть int"),
            (None, "1241251", "conversation_id не может быть None"),
            (13007796, -1241251, "admin_id должен быть > 0"),
            (13007796, "-1241251", "admin_id должен быть > 0"),
            (13007796, "awasdsd", "admin_id должен быть int"),
            (13007796, None, "admin_id не может быть None"),
        ],
    )
    async def test_init_game_error_init(
        self, application, mock_questions, conversation_id, admin_id, text_error
    ):
        with pytest.raises(ValueError, match=text_error):
            GameBlitz(
                application,
                conversation_id=conversation_id,
                admin_id=admin_id,
                questions=mock_questions,
            )
