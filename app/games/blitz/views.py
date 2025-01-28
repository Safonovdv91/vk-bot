from aiohttp_apispec import (
    docs,
    querystring_schema,
    request_schema,
    response_schema,
)

from app.games.blitz.schemes import BlitzGameStartQuerySchema, BlitzGameStopQuerySchema
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


class BlitzGameStopView(AuthRequiredMixin, View):
    @docs(
        tags=["Game Blitz"],
        summary="Закончить игру Blitz",
        description="""
        ----
        - conversation_id -  id чата в котором необходимо закончить игру blitz
        """,
    )
    @querystring_schema(BlitzGameStopQuerySchema)
    async def patch(self):
        conversation_id = self.request.query.get("conversation_id")

        await self.store.game_manager.stop_game(conversation_id=conversation_id)

        return json_response(data={"status": "Игра остановлена"})
