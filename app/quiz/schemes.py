from marshmallow import Schema, fields, validate


class ThemeSchema(Schema):
    id = fields.Int(required=False)
    title = fields.Str(required=True)
    description = fields.Str(required=False)


class AnswerSchema(Schema):
    id = fields.Int(required=False)
    title = fields.Str(required=True)
    score = fields.Int(required=True, validate=validate.Range(min=1, max=99))


class QuestionSchema(Schema):
    id = fields.Int(required=False)
    title = fields.Str(required=True)
    theme_id = fields.Int(required=True)
    answers = fields.Nested(
        AnswerSchema,
        many=True,
        required=True,
        validate=validate.Length(min=2, max=10),
    )


class ThemeListQuerySchema(Schema):
    limit = fields.Int(required=False, validate=validate.Range(min=1))
    offset = fields.Int(required=False, validate=validate.Range(min=1))


class ThemeListSchema(Schema):
    themes = fields.Nested(ThemeSchema, many=True)


class ThemeIdSchema(Schema):
    theme_id = fields.Int(required=True, validate=validate.Range(min=1))


class ThemeQueryIdSchema(ThemeIdSchema):
    offset = fields.Int(required=False, validate=validate.Range(min=1))
    limit = fields.Int(required=False, validate=validate.Range(min=1))


class QuestionIdSchema(Schema):
    question_id = fields.Int(validate=validate.Range(min=1))


class QuestionListSchema(Schema):
    questions = fields.Nested(QuestionSchema, many=True)


class QuestionPatchRequestsSchema(Schema):
    title = fields.Str(required=False)
    theme_id = fields.Int(required=False)
    # answers = fields.Nested(
    #     AnswerSchema,
    #     many=True,
    #     required=True,
    #     validate=validate.Length(min=2, max=10),
    # )
