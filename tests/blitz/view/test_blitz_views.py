import pytest
from aiohttp.test_utils import TestClient


class TestBlitzThemeAddView:
    async def test_unauthorized(self, cli: TestClient) -> None:
        response = await cli.post(
            "/game/blitz.themes_add",
            json={
                "title": "test_theme",
                "description": "test_description",
            },
        )
        assert response.status == 401

    @pytest.mark.parametrize(
        ("title", "description", "expected_status"),
        [
            ("", "test_description", 400),
            ("test_title", "", 200),
            ("test_title", "test_description", 200),
        ],
    )
    async def test_themes_add_success(
        self, auth_cli: TestClient, title: str, description: str, expected_status: int
    ) -> None:
        response = await auth_cli.post(
            "/game/blitz.themes_add",
            json={
                "title": title,
                "description": description,
            },
        )
        assert response.status == expected_status

    @pytest.mark.parametrize(
        ("title", "description", "expected_status"),
        [
            ("", "Good description", 400),
            ("", "", 400),
            (
                "Many wordssdasdasdasdasdasdasdasdasdasdasdasd"
                "asdasdasdasdasdasdasdasdasdasd"
                "asdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasd"
                "asdasdasdasdasdasdasdasdasd"
                "asdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasdas",
                "test_description",
                400,
            ),
        ],
    )
    async def test_themes_bad_title(
        self, auth_cli: TestClient, title: str, description: str, expected_status: int
    ) -> None:
        response = await auth_cli.post(
            "/game/blitz.themes_add",
            json={
                "title": title,
                "description": description,
            },
        )
        assert response.status == expected_status

    async def test_conflict_duplicate(self, auth_cli: TestClient) -> None:
        response = await auth_cli.post(
            "/game/blitz.themes_add",
            json={
                "title": "test_theme",
                "description": "test_description",
            },
        )
        assert response.status == 200
        response = await auth_cli.post(
            "/game/blitz.themes_add",
            json={
                "title": "test_theme",
                "description": "test_description",
            },
        )
        assert response.status == 409


class TestBlitzThemeGetView:
    URL = "/game/blitz.themes_list"

    async def test_unauthorized(self, cli: TestClient) -> None:
        response = await cli.get(self.URL)
        assert response.status == 401

    async def test_success_one_theme(
        self,
        auth_cli: TestClient,
        blitz_theme_1,
    ) -> None:
        response = await auth_cli.get(self.URL)
        assert response.status == 200

        data = await response.json()
        assert data == {
            "data": {
                "themes": [
                    {
                        "id": 1,
                        "title": "default test blitz theme",
                        "description": "test blitz theme description",
                    }
                ]
            },
            "status": "ok",
        }

    async def test_success_two_themes(
        self, auth_cli: TestClient, blitz_theme_1, blitz_theme_2
    ) -> None:
        response = await auth_cli.get(self.URL)
        assert response.status == 200

        data = await response.json()
        assert data == {
            "data": {
                "themes": [
                    {
                        "id": 1,
                        "title": "default test blitz theme",
                        "description": "test blitz theme description",
                    },
                    {
                        "id": 2,
                        "title": "default test blitz theme 2",
                        "description": None,
                    },
                ]
            },
            "status": "ok",
        }


class TestBlitzQuestionAddView:
    URL = "/game/blitz.questions_add"

    async def test_unauthorized(self, cli: TestClient) -> None:
        response = await cli.post(
            self.URL,
            json={
                "title": "Что в тяжелой коробке. что в ней?",
                "theme_id": 1,
                "answer": "Холодильник",
            },
        )
        assert response.status == 401, f"response = {response}"

        data = await response.json()
        assert data["status"] == "unauthorized"

    async def test_success_first_question(
        self, auth_cli: TestClient, blitz_theme_1
    ) -> None:
        response = await auth_cli.post(
            self.URL,
            json={
                "title": "Что в тяжелой коробке. что в ней?",
                "theme_id": 1,
                "answer": "Холодильник",
            },
        )
        assert response.status == 200, f"response = {response}"
        data = await response.json()
        assert data == {
            "status": "ok",
            "data": {
                "id": 1,
                "title": "Что в тяжелой коробке. что в ней?",
                "theme_id": 1,
                "answer": "Холодильник",
            },
        }

    async def test_success_second_question(
        self, auth_cli: TestClient, blitz_question_1
    ) -> None:
        response = await auth_cli.post(
            self.URL,
            json={
                "title": "Что в тяжелой коробке. что в ней?",
                "theme_id": 1,
                "answer": "Холодильник",
            },
        )
        assert response.status == 200, f"response = {response}"
        data = await response.json()
        assert data == {
            "status": "ok",
            "data": {
                "id": 2,
                "title": "Что в тяжелой коробке. что в ней?",
                "theme_id": 1,
                "answer": "Холодильник",
            },
        }

    async def test_error_no_themes(self, auth_cli: TestClient) -> None:
        response = await auth_cli.post(
            self.URL,
            json={
                "title": "Что в тяжелой коробке. что в ней?",
                "theme_id": 1,
                "answer": "Холодильник",
            },
        )
        assert response.status == 400, f"response = {response}"
        data = await response.json()
        assert data == {
            "data": {},
            "message": "не удалось добавить вопрос",
            "status": "bad_request",
        }

    @pytest.mark.parametrize(
        ("title", "answer", "expected_status"),
        [
            ("", "Good description", 400),
            ("", "", 400),
            (
                "Many wordssdasdasdasdasdasdasdasdasdasdasdasd"
                "asdasdasdasdasdasdasdasdasdasd"
                "asdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasd"
                "asdasdasdasdasdasdasdasdasd"
                "asdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasdas and it's  good",
                "test_description with more then 50 symbols answer and it's bad!"
                "test_description with more then 50 symbols answer and it's bad!"
                "test_description with more then 50 symbols answer and it's bad!",
                400,
            ),
        ],
    )
    async def test_errors_bad_data(
        self,
        auth_cli: TestClient,
        title: str,
        answer: str,
        expected_status: int,
        blitz_theme_1,
    ) -> None:
        response = await auth_cli.post(
            self.URL,
            json={
                "title": title,
                "theme_id": blitz_theme_1.id,
                "answer": answer,
            },
        )
        assert response.status == 400, f"response = {response}"
