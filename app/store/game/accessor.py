import typing
from collections.abc import Sequence

import sqlalchemy
from aiohttp.web_exceptions import HTTPBadRequest, HTTPNotFound
from asyncpg import UniqueViolationError
from sqlalchemy import desc, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import joinedload

from app.base.base_accessor import BaseAccessor
from app.game.constants import GameStage
from app.game.models import (
    Game,
    GameSettings,
    Player,
    PlayerAnswerGame,
)
from app.quiz.models import Answer, Question

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameAccessor(BaseAccessor):
    def __init__(self, app, *args, **kwargs):
        self.app = app
        super().__init__(app, *args, **kwargs)

        self.state_dict = {
            "init": GameStage.WAIT_INIT,
            "registration": GameStage.REGISTRATION_GAMERS,
            "wait_btn_answer": GameStage.WAITING_READY_TO_ANSWER,
            "wait_answer": GameStage.WAITING_ANSWER,
            "finished": GameStage.FINISHED,
            "canceled": GameStage.CANCELED,
        }

    async def add_game(
        self,
        peer_id: int,
    ) -> Game | None:
        async with self.app.database.session() as session:
            stmt = select(Question).order_by(func.random()).limit(1)
            result = await session.execute(stmt)
            question = result.scalar_one_or_none()

            if question is None:
                # выбросить кастомное исключение
                self.logger.error(
                    "В Базе данных отсутствует хотябы один вопрос!"
                )
                return None
            game = Game(
                conversation_id=peer_id,
                question=question,
                state=GameStage.WAIT_INIT,
            )
            session.add(game)
            await session.commit()

        return game

    async def change_pinned_message(self, game_id: int, id_pinned_message: int):
        async with self.app.database.session() as session:
            stmt = (
                update(Game)
                .where(Game.id == game_id)
                .values(pinned_conversation_message_id=id_pinned_message)
                .execution_options(synchronize_session="fetch")
            )

            try:
                await session.execute(stmt)
                await session.commit()
            except (
                sqlalchemy.exc.IntegrityError,
                sqlalchemy.exc.ProgrammingError,
            ) as exc:
                self.logger.exception(exc_info=exc, msg=exc)
                await (
                    session.rollback()
                )  # Откатываем транзакцию перед повторной попыткой
                raise HTTPBadRequest(
                    reason="Не удалось обновить pinned message из-за"
                    " проблемы целостности данных"
                ) from exc
                
    async def add_player(self, game_id: int, vk_user_id: int, name: str):
        player = Player(game_id=game_id, vk_user_id=vk_user_id, name=name)
        async with self.app.database.session() as session:
            try:
                session.add(player)
                await session.commit()

            except sqlalchemy.exc.IntegrityError as exc:
                await session.rollback()
                self.logger.exception(
                    exc_info=exc, msg="Не удалось зарегистрировать игрока"
                )

            except sqlalchemy.exc.InterfaceError as exc:
                await session.rollback()
                self.logger.exception(
                    exc_info=exc, msg="Не удалось зарегистрировать игрока"
                )
            except UniqueViolationError as exc:
                await session.rollback()
                self.logger.exception(
                    exc_info=exc, msg="Пользователь уже зарегестриован"
                )

    async def get_player_by_vk_id_game_id(self, vk_id: int, game_id):
        stmt = (
            select(Player)
            .where(Player.vk_user_id == vk_id)
            .where(Player.game_id == game_id)
        )

        async with self.app.database.session() as session:
            player = await session.execute(stmt)

        return player.scalar_one_or_none()

    async def delete_player(self, game_id: int, vk_user_id: int):
        async with self.app.database.session() as session:
            try:
                async with session.begin():
                    player = (
                        await session.execute(
                            select(Player)
                            .where(Player.game_id == game_id)
                            .where(Player.vk_user_id == vk_user_id)
                        )
                    ).scalar_one_or_none()
                    await session.delete(player)
                    await session.commit()
                    self.logger.info("Игрок с id %s удален", vk_user_id)

            except sqlalchemy.exc.IntegrityError as exc:
                await session.rollback()
                self.logger.exception(
                    exc_info=exc, msg="Не удалось удалить игрока"
                )

            except sqlalchemy.exc.InterfaceError as exc:
                await session.rollback()
                self.logger.exception(
                    exc_info=exc, msg="Не удалось удалить игрока"
                )

            else:
                return player

    async def change_state(self, game_id: int, new_state: GameStage):
        async with self.app.database.session() as session:
            stmt = (
                update(Game)
                .where(Game.id == game_id)
                .values(state=new_state)
                .execution_options(synchronize_session="fetch")
            )
            await session.execute(stmt)

            await session.commit()

    async def change_answer_player(self, game_id: int, vk_user_id: int):
        """Закрепить за игроком право на ответ
        указываем vk_id пользоывателя в игре
        :param game_id: id игры в которой принимается ответ
        :param vk_user_id: vk id пользователя от которого ждем ответ
        :return:
        """
        async with self.app.database.session() as session:
            stmt = (
                update(Game)
                .where(Game.id == game_id)
                .values(responsed_player_id=vk_user_id)
                .execution_options(synchronize_session="fetch")
            )
            await session.execute(stmt)
            await session.commit()

    async def change_admin_game_id(self, game_id: int, vk_user_id: int):
        async with self.app.database.session() as session:
            stmt = (
                update(Game)
                .where(Game.id == game_id)
                .values(admin_game_id=vk_user_id)
                .execution_options(synchronize_session="fetch")
            )
            await session.execute(stmt)
            await session.commit()

    async def get_game_by_peer_id(self, peer_id: int) -> Sequence[Game] | None:
        async with self.app.database.session() as session:
            result = await session.execute(
                select(Game)
                .where(Game.conversation_id == peer_id)
                .options(
                    joinedload(Game.question).joinedload(Question.answers),
                    joinedload(Game.players),
                )
            )
        return result.unique().scalar_one_or_none()

    async def get_game_by_id(self, id_: int):
        async with self.app.database.session() as session:
            result = await session.execute(
                select(Game)
                .where(Game.id == id_)
                .options(
                    joinedload(Game.question).joinedload(Question.answers),
                    joinedload(Game.players),
                    joinedload(Game.profile),
                    joinedload(Game.player_answers_games),
                )
            )
        return result.unique().scalar_one_or_none()

    async def player_add_answer_from_game(self, answer_id, player_id, game_id):
        """Функция добавления правильного ответа игрока для подсчета очков
        :param answer_id: id ответа на который ответил
        :param player_id: id игрока на который ответил
        :param game_id: id игры на который ответил игрок
        :return:
        """
        async with self.app.database.session() as session:
            player_answer_game = PlayerAnswerGame(
                answer_id=answer_id, player_id=player_id, game_id=game_id
            )
            session.add(player_answer_game)
            await session.commit()

    async def get_games_filtered_state(
        self,
        limit: int | None = None,
        offset: int | None = None,
        state: str | None = None,
    ):
        async with self.app.database.session() as session:
            stmt = select(Game).options(
                joinedload(Game.question).joinedload(Question.answers),
                joinedload(Game.players),
                joinedload(Game.player_answers_games).joinedload(
                    PlayerAnswerGame.answer
                ),
                joinedload(Game.profile),
                joinedload(Game.player_answers_games).joinedload(
                    PlayerAnswerGame.player
                ),
            )

            if state:
                try:
                    stmt = stmt.where(
                        Game.state == self.state_dict[state.lower()]
                    )
                except KeyError as exc:
                    raise HTTPBadRequest(
                        reason="Такого статуса не существует"
                    ) from exc

            if limit:
                stmt = stmt.limit(limit)

            if offset:
                stmt = stmt.offset(offset)

            result = await session.execute(stmt)
        return result.unique().scalars().all()

    async def get_active_games(
        self, limit: int | None = None, offset: int | None = None
    ):
        async with self.app.database.session() as session:
            stmt = (
                select(Game)
                .where(
                    Game.state.not_in([GameStage.FINISHED, GameStage.CANCELED])
                )
                .options(
                    joinedload(Game.question).joinedload(Question.answers),
                    joinedload(Game.players),
                    joinedload(Game.player_answers_games).joinedload(
                        PlayerAnswerGame.answer
                    ),
                    joinedload(Game.profile),
                    joinedload(Game.player_answers_games).joinedload(
                        PlayerAnswerGame.player
                    ),
                )
            )

            if limit:
                stmt = stmt.limit(limit)

            if offset:
                stmt = stmt.offset(offset)

            result = await session.execute(stmt)
        return result.unique().scalars().all()

    async def get_score(self, game_id: int):
        stmt = (
            select(
                Player.name.label("player_name"),
                func.sum(Answer.score).label("total_score"),
            )
            .join(PlayerAnswerGame, Player.id == PlayerAnswerGame.player_id)
            .join(Answer, PlayerAnswerGame.answer_id == Answer.id)
            .join(Game, PlayerAnswerGame.game_id == Game.id)
            .where(Game.id == game_id)
            .group_by(Player.id, Player.name)
            .order_by(desc("total_score"))
        )

        # Выполнение запроса и получение результатов
        async with self.app.database.session() as session:
            result = await session.execute(stmt)
            return result.all()  # Получение всех результатов запроса


class GameSettingsAccessor(BaseAccessor):
    async def connect(self, app: "Application") -> None:
        self.logger.info("Подключаем GameSettingsAccessor")

        game_settings = GameSettings(
            id=1,
            profile_name="default",
            description="Стандартная игра 100 к 1.\n "
            "Правила игры:\n"
            "Вам в чат будет выслан вопрос и необходимо "
            "предложить наиболее популярные ответы "
            " для того чтобы отвечать - необходимо нажать на"
            " кнопку, после чего будет "
            "предоставлено ограниченное время на ответ.\n"
            "Наиболее популярный ответ приносит больше всего очков.\n"
            " | XXXXXXX | (7) = 50 очков "
            "- ответ из 7 букв и принесет 50 очков.",
            time_to_registration=15,
            min_count_gamers=1,
            max_count_gamers=4,
            time_to_answer=15,
        )
        await self.upsert_settings(new_game_settings=game_settings)

    async def upsert_settings(self, new_game_settings: GameSettings):
        if (
            new_game_settings.min_count_gamers
            > new_game_settings.max_count_gamers
        ):
            raise HTTPBadRequest(
                reason="min_count_gamers не может быть"
                " больше max_count_gamers"
            )
        game_settings_data = {
            "profile_name": new_game_settings.profile_name,
            "description": new_game_settings.description,
            "time_to_registration": new_game_settings.time_to_registration,
            "min_count_gamers": new_game_settings.min_count_gamers,
            "max_count_gamers": new_game_settings.max_count_gamers,
            "time_to_answer": new_game_settings.time_to_answer,
        }

        stmt = insert(GameSettings).values(game_settings_data)
        stmt = stmt.on_conflict_do_nothing(index_elements=["profile_name"])

        async with self.app.database.session() as session:
            await session.execute(stmt)
            await session.commit()
            self.logger.info(
                "Создан новый профиль игры с именем %s",
                new_game_settings.profile_name,
            )

    async def get_by_id(self, id_: int):
        async with self.app.database.session() as session:
            result = await session.execute(
                select(GameSettings)
                .where(GameSettings.id == id_)
                .options(
                    joinedload(GameSettings.games),
                )
            )
            game_settings = result.unique().scalar_one_or_none()

            if not game_settings:
                raise HTTPNotFound(reason="Такого профиля не существует")

        return game_settings

    async def add_settings(self, new_game_settings: GameSettings):
        async with self.app.database.session() as session:
            if (
                new_game_settings.min_count_gamers
                > new_game_settings.max_count_gamers
            ):
                raise HTTPBadRequest(
                    reason="min_count_gamers не может быть"
                    " больше max_count_gamers"
                )
            session.add(new_game_settings)
            await session.commit()

    async def update_settings(
        self,
        id_: int,
        profile_name: str | None = None,
        description: str | None = None,
        time_to_registration: int | None = None,
        min_count_gamers: int | None = None,
        max_count_gamers: int | None = None,
        time_to_answer: int | None = None,
    ):
        async with self.app.database.session() as session:
            try:
                stmt = select(GameSettings).where(GameSettings.id == id_)
                result = await session.execute(stmt)
                game_settings = result.scalar_one_or_none()

                if not game_settings:
                    raise HTTPBadRequest(reason="Такой профиль не найден")

                stmt = update(GameSettings).where(GameSettings.id == id_)
                check_min_max(game_settings, min_count_gamers, max_count_gamers)

                if profile_name:
                    stmt = stmt.values(profile_name=profile_name)
                if description:
                    stmt = stmt.values(description=description)

                if time_to_registration:
                    stmt = stmt.values(
                        time_to_registration=int(time_to_registration)
                    )
                if time_to_answer:
                    stmt = stmt.values(time_to_answer=int(time_to_answer))
                if min_count_gamers:
                    stmt = stmt.values(min_count_gamers=int(min_count_gamers))
                if max_count_gamers:
                    stmt = stmt.values(max_count_gamers=int(max_count_gamers))

                await session.execute(stmt)
                await session.commit()

            except (
                sqlalchemy.exc.IntegrityError,
                sqlalchemy.exc.ProgrammingError,
            ) as exc:
                self.logger.exception(exc_info=exc, msg=exc)
                await (
                    session.rollback()
                )  # Откатываем транзакцию перед повторной попыткой
                raise HTTPBadRequest(
                    reason="Не удалось обновить вопрос из-за"
                    " проблемы целостности данных"
                ) from exc


def check_min_max(
    game_settings: GameSettings, min_count_gamers, max_count_gamers
):
    if min_count_gamers and max_count_gamers:
        if int(min_count_gamers) > int(max_count_gamers):
            raise HTTPBadRequest(
                reason="Минимальное кол-во игроков должно "
                "быть менньше максимального!!!"
            )
        return
    if (
        min_count_gamers
        and int(min_count_gamers) > game_settings.max_count_gamers
    ):
        raise HTTPBadRequest(
            reason=f"Минимальное кол-во игроков должно "
            f"быть меньше максимального {game_settings.max_count_gamers}"
        )

    if max_count_gamers and game_settings.min_count_gamers > int(
        max_count_gamers
    ):
        raise HTTPBadRequest(
            reason=f"Максимальное кол-во игроков должно "
            f"быть больше минимального ({game_settings.min_count_gamers})"
        )
