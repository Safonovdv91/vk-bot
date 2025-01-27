from marshmallow import (
    Schema,
    fields,
    validate,
)

from app.quiz.schemes import AnswerSchema, QuestionSchema


class BlitzGameStartQuerySchema(Schema):
    theme_id = fields.Int(required=False, validate=validate.Range(min=1))
    conversation_id = fields.Int(required=False, validate=validate.Range(min=1))
    admin_id = fields.Int(required=False, validate=validate.Range(min=1))
