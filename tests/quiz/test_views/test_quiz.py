from aiohttp.test_utils import TestClient


class TestQuestionAddView:
    async def test_unauthorized(self, cli: TestClient) -> None:
        response = await cli.get("/quiz.questions_add")

        assert response.status == 401, f"response = {response}"

        data = await response.json()
        assert data["status"] == "unauthorized"


class TestQuestionDeleteByIdView:
    async def test_unauthorized(self, cli: TestClient) -> None:
        response = await cli.get("/quiz.questions_delete_by_id")
        assert response.status == 401

        data = await response.json()
        assert data["status"] == "unauthorized"


class TestQuestionListView:
    async def test_unauthorized(self, cli: TestClient) -> None:
        response = await cli.get("/quiz.questions_list")
        assert response.status == 401

        data = await response.json()
        assert data["status"] == "unauthorized"


class TestThemeListView:
    async def test_unauthorized(self, cli: TestClient) -> None:
        response = await cli.get("/quiz.themes_list")
        assert response.status == 401

        data = await response.json()
        assert data["status"] == "unauthorized"


class TestThemeDeleteByIdView:
    async def test_unauthorized(self, cli: TestClient) -> None:
        response = await cli.get("/quiz.themes_delete_by_id")
        assert response.status == 401

        data = await response.json()
        assert data["status"] == "unauthorized"


class TestThemeAddView:
    async def test_unauthorized(self, cli: TestClient) -> None:
        response = await cli.get("/quiz.themes_add")
        assert response.status == 401

        data = await response.json()
        assert data["status"] == "unauthorized"
