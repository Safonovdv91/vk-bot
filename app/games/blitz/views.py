from aiohttp_apispec import (
    docs,
    querystring_schema,
)

from app.blitz.schemes import GameBlitzPatchSchema
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
