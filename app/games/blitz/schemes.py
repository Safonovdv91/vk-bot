from marshmallow import (
    Schema,
    fields,
    validate,
)


class BlitzGameStartQuerySchema(Schema):
    theme_id = fields.Int(required=False, validate=validate.Range(min=1))
    conversation_id = fields.Int(required=False, validate=validate.Range(min=1))
    admin_id = fields.Int(required=False, validate=validate.Range(min=1))


class BlitzGameStopQuerySchema(Schema):
    conversation_id = fields.Int(required=False, validate=validate.Range(min=1))
