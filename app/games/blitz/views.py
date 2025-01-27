from aiohttp_apispec import (
    docs,
    querystring_schema,
    request_schema,
    response_schema,
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
    async def patch(self):
        theme_id = self.request.query.get("time_to_registration")
        conversation_id = self.request.query.get("conversation_id")
        admin_id = self.request.query.get("admin_id")

        await self.store.game_manager.start_game(
            theme_id=theme_id, conversation_id=conversation_id, admin_id=admin_id
        )

        return json_response()


#
# class BlitzGameStartView(AuthRequiredMixin, View):
#     @docs(
#         tags=["Game Blitz"],
#         summary="Начать игрку Blitz",
#         description="""
#         ----
#         - theme_id  -  id темы, на которую начнется игра
#         - conversation_id -  id чата в котором начнется игра blitz
#         """,
#     )
#     @querystring_schema(BlitzGameStartQuerySchema)
#     async def patch(self):
#         theme_id = self.request.query.get("time_to_registration")
#         conversation_id = self.request.query.get("conversation_id")
#
#         await self.store.game_manager.handle_message(
#             message="/start_blitz",
#             theme_id=theme_id,
#             conversation_id=conversation_id,
#             user_id=1111
#         )
#
#
#         return json_response()
