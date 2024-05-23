from aiohttp.test_utils import TestClient


class TestListActive:
    async def test_unauthorized(self, cli: TestClient) -> None:
        response = await cli.get("/game.list_active")

        assert response.status == 401, f"response = {response}"

        data = await response.json()
        assert data["status"] == "unauthorized"

    async def test_success_empty_finished(
        self, auth_cli: TestClient, game_finished, game_canceled
    ) -> None:
        response = await auth_cli.get("/game.list_active")

        assert response.status == 200, f"response = {response}"

        data = await response.json()
        assert data == {"data": {"games": []}, "status": "ok"}

    async def test_success(self, auth_cli: TestClient, game_running) -> None:
        response = await auth_cli.get("/game.list_active")

        assert response.status == 200, f"response = {response}"

        data = await response.json()
        assert data == {
            "data": {
                "games": [
                    {
                        "id": 1,
                        "player_answers_games": [],
                        "players": [],
                        "profile": {
                            "description": None,
                            "id": 1,
                            "max_count_gamers": 6,
                            "min_count_gamers": 1,
                            "profile_name": "test",
                            "time_to_answer": 15,
                            "time_to_registration": 30,
                        },
                        "question": {
                            "answers": [
                                {"id": 4, "score": 15, "title": "животных"},
                                {"id": 3, "score": 15, "title": "природу"},
                                {"id": 2, "score": 27, "title": "свадьбу"},
                                {"id": 1, "score": 43, "title": "Еду"},
                            ],
                            "id": 1,
                            "theme_id": 1,
                            "title": "Кого или что чаще всего снимает "
                            "фотограф?",
                        },
                        "responsed_player_id": None,
                        "state": "GameStage.WAITING_ANSWER",
                    }
                ]
            },
            "status": "ok",
        }


class TestGetById:
    async def test_unauthorized(self, cli: TestClient) -> None:
        response = await cli.get("/game.get_by_id", params={"game_id": 1})

        assert response.status == 401, f"response = {response}"

        data = await response.json()
        assert data["status"] == "unauthorized"

    async def test_get_by_id_success(
        self, auth_cli: TestClient, game_running
    ) -> None:
        response = await auth_cli.get("/game.get_by_id", params={"game_id": 1})

        assert response.status == 200, f"response = {response}"

        data = await response.json()
        assert data == {
            "data": {
                "id": 1,
                "player_answers_games": [],
                "players": [],
                "profile": {
                    "description": None,
                    "id": 1,
                    "max_count_gamers": 6,
                    "min_count_gamers": 1,
                    "profile_name": "test",
                    "time_to_answer": 15,
                    "time_to_registration": 30,
                },
                "question": {
                    "answers": [
                        {"id": 1, "score": 43, "title": "Еду"},
                        {"id": 2, "score": 27, "title": "свадьбу"},
                        {"id": 3, "score": 15, "title": "природу"},
                        {"id": 4, "score": 15, "title": "животных"},
                    ],
                    "id": 1,
                    "theme_id": 1,
                    "title": "Кого или что чаще всего снимает фотограф?",
                },
                "responsed_player_id": None,
                "state": "GameStage.WAITING_ANSWER",
            },
            "status": "ok",
        }

    async def test_get_by_id_success_no_game(
        self, auth_cli: TestClient, game_running
    ) -> None:
        response = await auth_cli.get("/game.get_by_id", params={"game_id": 2})

        assert response.status == 200, f"response = {response}"

        data = await response.json()
        assert data == {"data": {}, "status": "ok"}

    async def test_get_by_id_success_bad_id(
        self, auth_cli: TestClient, game_running
    ) -> None:
        response = await auth_cli.get(
            "/game.get_by_id", params={"game_id": "sd"}
        )

        assert response.status == 400, f"response = {response}"

        data = await response.json()
        assert data == {
            "data": {"querystring": {"game_id": ["Not a valid integer."]}},
            "message": "Unprocessable Entity",
            "status": "bad_request",
        }
