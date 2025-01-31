from aiohttp_apispec import (
    docs,
    querystring_schema,
    response_schema,
)

from app.blitz.schemes import (
    BlitzGameListQueryFilteredSchema,
    BlitzGameListSchema,
    GameBlitzPatchSchema,
    QueryLimitOffsetSchema,
)
from app.games.blitz.schemes import BlitzGameStartQuerySchema
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response


class BlitzGameStartView(AuthRequiredMixin, View):
    @docs(
        tags=["Game Blitz"],
        summary="Начать игрку Blitz",
        description="""
        ----
        - theme_id  -  id темы, на которую начнется игра
        - conversation_id -  id чата в котором начнется игра blitz
        - admin_id -  id администратора игры(тот кто может прекратить её из чата)
        """,
    )
    @querystring_schema(BlitzGameStartQuerySchema)
    async def post(self):
        theme_id = self.request.query.get("time_to_registration")
        conversation_id = self.request.query.get("conversation_id")
        admin_id = self.request.query.get("admin_id")

        await self.store.game_manager.start_game(
            theme_id=theme_id, conversation_id=conversation_id, admin_id=admin_id
        )

        return json_response(
            data={"status": "Игра начата", "conversation_id": conversation_id}
        )


class BlitzGameChangeStatusView(AuthRequiredMixin, View):
    @docs(
        tags=["Game Blitz"],
        summary="Закончить игру Blitz",
        description="""
        ----
        - game_id - id игры
        - new_status_game - в какой статус необходимо перевести     
        """,
    )
    @querystring_schema(GameBlitzPatchSchema)
    async def patch(self):
        state = self.request.query.get("state")
        game_id = int(self.request.query.get("game_id"))
        await self.store.blitzes.change_state(game_id=game_id, new_state=state)

        return json_response(data={"status": "Игра остановлена"})


class BlitzGameListView(AuthRequiredMixin, View):
    @docs(
        tags=["Game Blitz"],
        summary="Получить игры в зависимости от состояния",
        description="""
        Возвращает все игры по выбранному 
        ----
        limit - количество игр на странице
        offset - смещение
        state_filter - фильтр по состоянию игры
        ---- state ----
        WAITING_ANSWER - Игра идет, и ожидаем ответа на вопрос
        PAUSE - Игра приостановлена
        FINISHED - Игра успешно завершена (Баллы игры записаны)
        CANCELED - Игра отменена (Баллы игры не записаны)

        В случае пустых значений - возвращает все что есть.
        """,
    )
    @querystring_schema(BlitzGameListQueryFilteredSchema)
    @response_schema(BlitzGameListSchema)
    async def get(self):
        limit = self.request.query.get("limit")
        offset = self.request.query.get("offset")
        state = self.request.query.get("state")
        games = await self.store.blitzes.get_games_by_state(
            limit=limit, offset=offset, state=state
        )

        return json_response(data=BlitzGameListSchema().dump({"games": games}))


class BlitzGameActiveListView(AuthRequiredMixin, View):
    @docs(
        tags=["Game Blitz"],
        summary="Получить активные игры (PAUSE / WAITING_ANSWER) "
        "игры в зависимости от состояния",
        description="""
        Возвращает все игры по выбранному 
        ----
        limit - количество игр на странице
        offset - смещение
        ---- state ----
        WAITING_ANSWER - Игра идет, и ожидаем ответа на вопрос
        PAUSE - Игра приостановлена
        """,
    )
    @querystring_schema(QueryLimitOffsetSchema)
    @response_schema(BlitzGameListSchema)
    async def get(self):
        limit = self.request.query.get("limit")
        offset = self.request.query.get("offset")
        games = await self.store.blitzes.get_active_games(limit=limit, offset=offset)

        return json_response(data=BlitzGameListSchema().dump({"games": games}))
