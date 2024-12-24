from marshmallow import Schema, fields, validate


class BlitzThemeSchema(Schema):
    id = fields.Int(required=False)
    title = fields.Str(required=True)
    description = fields.Str(required=False)


class BlitzQuestionSchema(Schema):
    id = fields.Int(required=False)
    title = fields.Str(required=True)
    theme_id = fields.Int(required=True)
    answer = fields.Str(required=True)


class BlitzThemeListQuerySchema(Schema):
    limit = fields.Int(required=False, validate=validate.Range(min=1))
    offset = fields.Int(required=False, validate=validate.Range(min=1))


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
