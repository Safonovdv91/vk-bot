from collections.abc import Sequence

import sqlalchemy
from asyncpg import UniqueViolationError
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import joinedload

from app.base.base_accessor import BaseAccessor
from app.game.models import Game, GameStage, Player, PlayerAnswerGame
from app.quiz.models import Question


class GameAccessor(BaseAccessor):
    async def add_game(
        self,
        peer_id: int,
    ) -> Sequence[Game] | None:
        async with self.app.database.session() as session:
            stmt = select(Question).order_by(func.random()).limit(1)
            result = await session.execute(stmt)
            question = result.scalar_one_or_none()

            if question is None:
                # выбросить кастомное исключение
                return None

            game_data = {
                "conversation_id": peer_id,
                "question_id": question.id,
                "state": GameStage.WAIT_INIT,
            }

            stmt = insert(Game).values(game_data)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["conversation_id"]
            )
            await session.execute(stmt)
            await session.commit()

        return await self.get_game_by_peer_id(peer_id)

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
                .where(Question.id == id_)
                .options(joinedload(Question.answers))
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

    async def get_all_games(self):
        async with self.app.database.session() as session:
            result = await session.execute(
                select(Game)
                .where(Game.state.not_in([GameStage.FINISHED, GameStage.CANCELED]))
                .options(
                    joinedload(Game.question).joinedload(Question.answers),
                    joinedload(Game.players),
                )
            )
        return result.unique().scalars().all()
