from aiohttp_apispec import (
    docs,
    querystring_schema,
    request_schema,
    response_schema,
)

from app.game.models import GameSettings
from app.game.schemes import (
    GameIdSchema,
    GameListQueryFilteredSchema,
    GameListQuerySchema,
    GameListSchema,
    GameSchema,
    GameSettingsSchema,
    SettingsIdSchema,
)
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response


class GameListView(AuthRequiredMixin, View):
    @docs(
        tags=["Game"],
        summary="Получить все игры",
        description="Отобразить все игры",
    )
    @querystring_schema(GameListQueryFilteredSchema)
    @response_schema(GameListSchema)
    async def get(self):
        limit = self.request.query.get("limit")
        offset = self.request.query.get("offset")
        state = self.request.query.get("state")

        return json_response(
            data=GameListSchema().dump(
                {
                    "games": await self.store.game_accessor.get_games_filtered_state(
                        limit=limit, offset=offset, state=state
                    )
                }
            )
        )


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

        return json_response(
            data=GameListSchema().dump(
                {
                    "games": await self.store.game_accessor.get_active_games(
                        limit=limit, offset=offset
                    )
                }
            )
        )


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

        return json_response(
            data=GameSchema().dump(
                await self.store.game_accessor.get_game_by_id(id_=game_id)
            )
        )


class SettingsGetByIdView(AuthRequiredMixin, View):
    @docs(
        tags=["Game", "Settings"],
        summary="Получить settings по id",
        description="Отобразить по настройка",
    )
    @querystring_schema(SettingsIdSchema)
    @response_schema(GameSettingsSchema)
    async def get(self):
        profile_id = int(self.request.query.get("profile_id"))

        return json_response(
            data=GameSettingsSchema().dump(
                await self.store.game_settings_accessor.get_by_id(
                    id_=profile_id
                )
            )
        )


class SettingsAddView(AuthRequiredMixin, View):
    @docs(
        tags=["Game", "Settings"],
        summary="Добавить новую тему",
        description="Добавить новый профиль в со своими настройками",
    )
    @request_schema(GameSettingsSchema)
    @response_schema(GameSettingsSchema)
    async def post(self):
        game_settings = GameSettings(
            profile_name=self.data.get("profile_name"),
            description=self.data.get("description"),
            time_to_registration=self.data.get("time_to_registration"),
            min_count_gamers=self.data.get("min_count_gamers"),
            max_count_gamers=self.data.get("max_count_gamers"),
            time_to_answer=self.data.get("time_to_answer"),
        )

        return json_response(
            data=GameSettingsSchema().dump(
                await self.store.game_settings_accessor.add_settings(
                    game_settings
                )
            )
        )
