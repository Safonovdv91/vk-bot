from aiohttp_apispec import (
    docs,
    querystring_schema,
    response_schema,
)

from app.game.schemes import (
    GameIdSchema,
    GameListQuerySchema,
    GameListSchema,
    GameSchema,
)
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response


class GameProfileListActiveView(AuthRequiredMixin, View):
    @docs(
        tags=["Game"],
        summary="Получить активные игры",
        description="Отобразить активные игры, которые идут"
        " в настоящий момент времени",
    )
    @querystring_schema(GameListQuerySchema)
    @response_schema(GameListSchema)
    async def get(self):
        limit = self.request.query.get("limit")
        offset = self.request.query.get("offset")
        games = await self.store.game_accessor.get_active_games(
            limit=limit, offset=offset
        )

        return json_response(data=GameListSchema().dump({"games": games}))


class GameGetByIdView(AuthRequiredMixin, View):
    @docs(
        tags=["Game"],
        summary="Получить игру по id",
        description="Отобразить подробную информацию по игре",
    )
    @querystring_schema(GameIdSchema)
    @response_schema(GameSchema)
    async def get(self):
        game_id = int(self.request.query.get("game_id"))
        game = await self.store.game_accessor.get_game_by_id(id_=game_id)

        return json_response(data=GameSchema().dump(game))
