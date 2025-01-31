from marshmallow import Schema, fields, validate

from app.games.blitz.constants import BlitzGameStage


class BlitzThemeSchema(Schema):
    id = fields.Int(required=False)
    title = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    description = fields.Str(required=False, validate=validate.Length(min=None, max=500))


class BlitzQuestionSchema(Schema):
    id = fields.Int(required=False)
    title = fields.Str(required=True, validate=validate.Length(min=1, max=500))
    theme_id = fields.Int(required=False, default=1, validate=validate.Range(min=1))
    answer = fields.Str(required=True, validate=validate.Length(min=1, max=100))


class BlitzThemeListQuerySchema(Schema):
    limit = fields.Int(required=False, validate=validate.Range(min=1))
    offset = fields.Int(required=False, validate=validate.Range(min=1))


class BlitzThemeListSchema(Schema):
    themes = fields.Nested(BlitzThemeSchema, many=True)


class BlitzThemeIdSchema(Schema):
    theme_id = fields.Int(required=True, validate=validate.Range(min=1))


class BlitzThemeQueryIdSchema(BlitzThemeIdSchema):
    offset = fields.Int(required=False, validate=validate.Range(min=1))
    limit = fields.Int(required=False, validate=validate.Range(min=1))


class BlitzQuestionIdSchema(Schema):
    question_id = fields.Int(validate=validate.Range(min=1))


class BlitzQuestionListSchema(Schema):
    questions = fields.Nested(BlitzQuestionSchema, many=True)


class BlitzQuestionPatchRequestsSchema(Schema):
    title = fields.Str(required=False)
    theme_id = fields.Int(required=False)
    # answers = fields.Nested(
    #     AnswerSchema,
    #     many=True,
    #     required=True,
    #     validate=validate.Length(min=2, max=10),
    # )


class GameBlitzPatchSchema(Schema):
    game_id = fields.Int(required=True, validate=validate.Range(min=1))
    state = fields.Str(
        required=True,
        validate=validate.OneOf(
            [state.value for state in BlitzGameStage],
            error="Недопустимое значение для поля state.",
        ),
    )


class GameBlitzGetSchema(Schema):
    game_id = fields.Int(required=True, validate=validate.Range(min=1))
    state = fields.Str(
        required=True,
        validate=validate.OneOf(
            [state.value for state in BlitzGameStage],
            error="Недопустимое значение для поля state.",
        ),
    )
