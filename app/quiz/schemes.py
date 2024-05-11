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
    answers = fields.Nested(AnswerSchema, many=True, required=True)


class ThemeListSchema(Schema):
    themes = fields.Nested(ThemeSchema, many=True)


class ThemeIdSchema(Schema):
    theme_id = fields.Int()


class QuestionIdSchema(Schema):
    question_id = fields.Int()


class ListQuestionSchema(Schema):
    questions = fields.Nested(QuestionSchema, many=True)
