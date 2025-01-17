from marshmallow import Schema, fields, validate


class VkMessageListQuerySchema(Schema):
    conversation_id = fields.Int(required=False)
    limit = fields.Int(required=False, validate=validate.Range(min=1))
    offset = fields.Int(required=False, validate=validate.Range(min=1))


class VkMessageSchema(Schema):
    id = fields.Int(required=False)
    conversation_id = fields.Int(required=True)
    text = fields.Str(required=True)
    user_id = fields.Int(required=True)
    date = fields.DateTime(required=False)


class VkMessageListSchema(Schema):
    vk_messages = fields.Nested(VkMessageSchema, many=True)
