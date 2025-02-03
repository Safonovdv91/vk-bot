from aiohttp.web_exceptions import HTTPBadRequest
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
from app.games.blitz.constants import BlitzGameStage
from app.games.blitz.schemes import BlitzGameStartQuerySchema
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response


class BlitzGameStartView(AuthRequiredMixin, View):
    @docs(
        tags=["Game Blitz Management"],
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
        theme_id = self.request.query.get("theme_id")
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
        tags=["Game Blitz Management"],
        summary="Изменить статус игры",
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

        if state == "PAUSE":
            game = await self.store.blitzes.change_state(
                game_id=game_id, new_state=BlitzGameStage.PAUSE
            )
            await self.store.game_manager.pause_game(conversation_id=game.conversation_id)
            msg = "Игра приостановлена"

        elif state == "FINISHED":
            game = await self.store.blitzes.change_state(
                game_id=game_id, new_state=BlitzGameStage.FINISHED
            )
            await self.store.game_manager.finish_game(
                conversation_id=game.conversation_id
            )
            msg = "Игра завершена"

        elif state == "CANCELED":
            game = await self.store.blitzes.change_state(
                game_id=game_id, new_state=BlitzGameStage.CANCELED
            )
            await self.store.game_manager.cancel_game(
                conversation_id=game.conversation_id
            )
            msg = "Игра отменена"

        elif state == "WAITING_ANSWER":
            game = await self.store.blitzes.get_game_by_id(game_id=game_id)
            if game.game_stage == BlitzGameStage.PAUSE:
                await self.store.blitzes.change_state(
                    game_id=game_id, new_state=BlitzGameStage.WAITING_ANSWER
                )
                await self.store.game_manager.resume_game(game_model=game)
                msg = "Игра продолжается и ожидает ответа"
            else:
                raise HTTPBadRequest(reason="Игра не в состоянии PAUSE")

        else:
            msg = "Неизвестный статус игры"

        return json_response(data={"status": msg})


class BlitzGameListView(AuthRequiredMixin, View):
    @docs(
        tags=["Game Blitz Managment"],
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
        tags=["Game Blitz Management"],
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
