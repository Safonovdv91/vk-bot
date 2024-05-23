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
                            "min_count_gamers": 2,
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


class TestGetGameById:
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
                    "min_count_gamers": 2,
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


class TestGameSettingsGetById:
    async def test_unauthorized(self, cli: TestClient) -> None:
        response = await cli.get(
            "game/profile.get_by_id", params={"profile_id": 1}
        )

        assert response.status == 401, f"response = {response}"

        data = await response.json()
        assert data["status"] == "unauthorized"

    async def test_success(self, auth_cli: TestClient, game_settings) -> None:
        response = await auth_cli.get(
            "game/profile.get_by_id", params={"profile_id": 1}
        )

        assert response.status == 200, f"response = {response}"

        data = await response.json()
        assert data == {
            "data": {
                "description": None,
                "id": 1,
                "max_count_gamers": 6,
                "min_count_gamers": 2,
                "profile_name": "test",
                "time_to_answer": 15,
                "time_to_registration": 30,
            },
            "status": "ok",
        }

    async def test_success_bad_id(
        self, auth_cli: TestClient, game_settings
    ) -> None:
        response = await auth_cli.get(
            "game/profile.get_by_id", params={"profile_id": "sd"}
        )
        assert response.status == 400, f"response = {response}"
        data = await response.json()

        assert data == {
            "data": {"querystring": {"profile_id": ["Not a valid integer."]}},
            "message": "Unprocessable Entity",
            "status": "bad_request",
        }


class TestChangeProfile:
    async def test_unauthorized(self, cli: TestClient) -> None:
        response = await cli.get(
            "game/profile.default", params={"time_to_registration": 12}
        )

        assert response.status == 401, f"response = {response}"

        data = await response.json()
        assert data["status"] == "unauthorized"

    async def test_success(self, auth_cli: TestClient, game_settings) -> None:
        response = await auth_cli.patch(
            "game/profile.default", params={"time_to_registration": 122}
        )

        assert response.status == 200, f"response = {response}"

        data = await response.json()
        assert data == {"data": {}, "status": "ok"}

        response = await auth_cli.get(
            "game/profile.get_by_id", params={"profile_id": 1}
        )
        assert response.status == 200

        data = await response.json()
        assert (
            data
            == {
                "data": {
                    "description": None,
                    "id": 1,
                    "max_count_gamers": 6,
                    "min_count_gamers": 2,
                    "profile_name": "test",
                    "time_to_answer": 15,
                    "time_to_registration": 122,
                },
                "status": "ok",
            }
            != {"data": {}, "status": "ok"}
        )

    async def test_success_min_max(
        self, auth_cli: TestClient, game_settings
    ) -> None:
        response = await auth_cli.patch(
            "game/profile.default",
            params={
                "min_count_gamers": 3,
                "max_count_gamers": 7,
            },
        )

        assert response.status == 200, f"response = {response}"

        data = await response.json()
        assert data == {"data": {}, "status": "ok"}

        response = await auth_cli.get(
            "game/profile.get_by_id", params={"profile_id": 1}
        )
        assert response.status == 200

        data = await response.json()
        assert data == {
            "data": {
                "description": None,
                "id": 1,
                "max_count_gamers": 7,
                "min_count_gamers": 3,
                "profile_name": "test",
                "time_to_answer": 15,
                "time_to_registration": 30,
            },
            "status": "ok",
        }

    async def test_success_bad_max(
        self, auth_cli: TestClient, game_settings
    ) -> None:
        response = await auth_cli.patch(
            "game/profile.default",
            params={
                "max_count_gamers": 1,
            },
        )

        assert response.status == 400, f"response = {response}"

        data = await response.json()
        assert data == {
            "data": {},
            "message": "Максимальное кол-во игроков должно быть"
            " больше минимального (2)",
            "status": "bad_request",
        }
