from aiohttp_apispec import docs, querystring_schema, response_schema

from app.vk.schemes import VkMessageListQuerySchema, VkMessageListSchema
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response


class MessagesListView(AuthRequiredMixin, View):
    @docs(
        tags=["Vk_messages"],
        summary="Отобразить список сообщений vk",
        description="""
        Отобразить список сообщений в беседе -
        conversation_id - идентификатор беседы 
        (для личной беседы это идентификатор пользователя)
        limit и offset - для ограничения выборки
        """,
    )
    @querystring_schema(VkMessageListQuerySchema)
    @response_schema(VkMessageListSchema)
    async def get(self):
        conversation_id = int(self.request.query.get("conversation_id"))
        limit = self.request.query.get("limit")
        offset = self.request.query.get("offset")
        messages = await self.store.vk_messages.get_messages_list(
            conversation_id, offset, limit
        )
        data = VkMessageListSchema().dump({"vk_messages": messages})

        return json_response(data=data)
