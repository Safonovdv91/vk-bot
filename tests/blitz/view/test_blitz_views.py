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

    async def test_success(self, auth_cli: TestClient) -> None:
        response = await auth_cli.post(
            "/game/blitz.themes_add",
            json={
                "title": "test_theme",
                "description": "test_description",
            },
        )
        assert response.status == 200

    async def test_success_no_description(self, auth_cli: TestClient) -> None:
        response = await auth_cli.post(
            "/game/blitz.themes_add",
            json={
                "title": "test_theme",
            },
        )
        assert response.status == 200

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

    async def test_bad_title(self, auth_cli: TestClient) -> None:
        response = await auth_cli.post(
            "/game/blitz.themes_add",
            json={
                "title": "",
                "description": "test_description",
            },
        )
        assert response.status == 400

    async def test_no_title(self, auth_cli: TestClient) -> None:
        response = await auth_cli.post(
            "/game/blitz.themes_add",
            json={
                "description": "test_description",
            },
        )
        assert response.status == 400
