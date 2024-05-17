from marshmallow import Schema, fields, validate

from app.quiz.schemes import AnswerSchema, QuestionSchema


class GameSettingsSchema(Schema):
    id = fields.Int(required=False)
    profile_name = fields.Str(required=True)
    description = fields.Str(required=True)


class GameListQuerySchema(Schema):
    limit = fields.Int(required=False, validate=validate.Range(min=1))
    offset = fields.Int(required=False, validate=validate.Range(min=1))


class PlayerSchema(Schema):
    vk_user_id = fields.Int(required=True)
    name = fields.Str(required=True)


class PlayerAnswersGames(Schema):
    answer = fields.Nested(AnswerSchema)
    player = fields.Nested(PlayerSchema)


class GameSchema(Schema):
    id = fields.Int(required=False)
    description = fields.Str(required=False)
    responsed_player_id = fields.Str(required=True)
    state = fields.Str(required=True)
    profile_id = fields.Str(required=True)
    profile = fields.Nested(GameSettingsSchema, required=True)
    question = fields.Nested(QuestionSchema, many=False, required=True)
    players = fields.Nested(PlayerSchema, many=True, required=True)
    player_answers_games = fields.Nested(
        PlayerAnswersGames, many=True, required=True
    )


class GameListSchema(Schema):
    games = fields.Nested(GameSchema, many=True)


class GameIdSchema(Schema):
    game_id = fields.Int(validate=validate.Range(min=1))
