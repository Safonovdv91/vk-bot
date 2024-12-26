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
