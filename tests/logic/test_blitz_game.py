from unittest.mock import AsyncMock, patch

import pytest

from app.games.blitz.logic import BlitzGameStage, GameBlitz
from app.store.vk_api.dataclasses import VkUser


class TestBlitzGameSuccess:
    @pytest.mark.parametrize(
        ("conversation_id", "admin_id"),
        [
            (13007796, 13007796),
            ("13007796", "13007796"),
        ],
    )
    @pytest.mark.logic
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
        assert game_blitz.game_stage == BlitzGameStage.WAIT_ANSWER


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
    @pytest.mark.logic
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


class TestBlitzGameHandleMessage:
    """Интеграционный тест всей игры отработает ли она"""

    async def _handle_and_assert(
        self, game_blitz, message, expected_question_id, expected_stage
    ):
        await game_blitz.handle_message(
            message=message,
            user_id=13007796,
            conversation_id=13007796,
        )
        assert game_blitz.id_current_question == expected_question_id
        assert game_blitz.game_stage == expected_stage

    @pytest.mark.logic
    async def test_take_answer_success(self, application, mock_questions):
        game_blitz = GameBlitz(
            application,
            conversation_id=13007796,
            admin_id=13007796,
            questions=mock_questions,
        )
        assert game_blitz.game_stage == BlitzGameStage.WAIT_ANSWER
        assert game_blitz.id_current_question == 0

        # Создаём мок для метода get_vk_user
        with (
            patch.object(
                application.store.vk_api, "get_vk_user", new_callable=AsyncMock
            ) as mock_get_vk_user,
            patch.object(
                application.store.vk_api, "send_message", new_callable=AsyncMock
            ),
        ):
            # Определяем, что метод должен вернуть
            mock_get_vk_user.return_value = VkUser(
                id=13007796, first_name="test", last_name="test"
            )

            # Обработка первого сообщения
            await self._handle_and_assert(
                game_blitz,
                message=mock_questions[0].answer,
                expected_question_id=1,
                expected_stage=BlitzGameStage.WAIT_ANSWER,
            )

            # Обработка второго сообщения
            await self._handle_and_assert(
                game_blitz,
                message=mock_questions[1].answer,
                expected_question_id=2,
                expected_stage=BlitzGameStage.FINISHED,
            )

    @pytest.mark.parametrize(
        ("user_message", "user_id", "conversations_id", "type_error", "text_error"),
        [
            (None, 13007796, 13007796, TypeError, "message не может быть None"),
            ("Answer 1", None, 13007796, TypeError, "user_id не может быть None"),
            ("Answer 1", 13007796, None, TypeError, "conversation_id не может быть None"),
        ],
    )
    @pytest.mark.logic
    async def test_take_answer_bad_data(
        self,
        application,
        mock_questions,
        user_message,
        type_error,
        text_error,
        user_id,
        conversations_id,
    ):
        game_blitz = GameBlitz(
            application,
            conversation_id=13007796,
            admin_id=13007796,
            questions=mock_questions,
        )
        with pytest.raises(type_error, match=text_error):
            await game_blitz.handle_message(
                message=user_message, user_id=user_id, conversation_id=conversations_id
            )
