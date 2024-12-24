from marshmallow import (
    Schema,
    fields,
    validate,
)

from app.quiz.schemes import AnswerSchema, QuestionSchema


class GameSettingsIdSchema(Schema):
    profile_id = fields.Int(validate=validate.Range(min=1), required=True)


class DefaultGameSettingsIdSchema(Schema):
    time_to_registration = fields.Int(
        required=False, validate=validate.Range(min=1)
    )
    min_count_gamers = fields.Int(
        required=False, validate=validate.Range(min=1)
    )
    max_count_gamers = fields.Int(
        required=False, validate=validate.Range(min=1, max=30)
    )
    time_to_answer = fields.Int(
        required=False, validate=validate.Range(min=1, max=999)
    )


class GameSettingsPatchSchema(Schema):
    profile_name = fields.Str(required=False)
    description = fields.Str(required=False)
    time_to_registration = fields.Int(
        required=False, validate=validate.Range(min=1)
    )
    min_count_gamers = fields.Int(
        required=False, validate=validate.Range(min=1)
    )
    max_count_gamers = fields.Int(
        required=False, validate=validate.Range(min=1, max=30)
    )
    time_to_answer = fields.Int(
        required=False, validate=validate.Range(min=1, max=999)
    )


class GameSettingsPatchRequestsSchema(Schema):
    profile_name = fields.Str(
        required=False,
        validate=validate.Length(min=1, max=20),
    )
    time_to_registration = fields.Str(required=False)
    min_count_gamers = fields.Int(required=False)
    max_count_gamers = fields.Int(required=False)
    time_to_answer = fields.Int(required=False)
    description = fields.Str(required=False)


class GameSettingsSchema(Schema):
    id = fields.Int(required=False)
    profile_name = fields.Str(required=True)
    description = fields.Str(required=True)
    time_to_registration = fields.Int(
        required=True, validate=validate.Range(min=1)
    )
    min_count_gamers = fields.Int(required=True, validate=validate.Range(min=1))
    max_count_gamers = fields.Int(
        required=True, validate=validate.Range(min=1, max=15)
    )
    time_to_answer = fields.Int(
        required=True, validate=validate.Range(min=1, max=99)
    )


class GameListQuerySchema(Schema):
    limit = fields.Int(required=False, validate=validate.Range(min=1))
    offset = fields.Int(required=False, validate=validate.Range(min=1))


class GameListQueryFilteredSchema(Schema):
    limit = fields.Int(required=False, validate=validate.Range(min=1))
    offset = fields.Int(required=False, validate=validate.Range(min=1))
    state = fields.Str(
        required=False,
        validate=validate.OneOf(
            [
                "registration",
                "wait_btn_answer",
                "wait_answer",
                "finished",
                "canceled",
            ],
            error="Недопустимое значение для поля state.",
        ),
    )


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


class SettingsIdSchema(Schema):
    profile_id = fields.Int(validate=validate.Range(min=1))
