from collections.abc import Sequence

from sqlalchemy import func, not_, select

from app.base.base_accessor import BaseAccessor
from app.game.models import Game, GameStage, Player
from app.quiz.models import Question


class GameAccessor(BaseAccessor):
    async def add_game(
        self,
        peer_id: int,
    ) -> Game:
        async with self.app.database.session() as session:
            stmt = select(Question).order_by(func.random()).limit(1)
            result = await session.execute(stmt)
            question = result.scalar_one_or_none()
            game = Game(
                conversation_id=peer_id,
                question_id=question.id,
                game_stage=GameStage.REGISTRATION_GAMERS,
            )
            session.add(game)
            await session.commit()

        return game

    async def add_player(self, game_id: int, vk_user_id: int, name: str):
        player = Player(game_id=game_id, vk_user_id=vk_user_id, name=name)

        async with self.app.database.session() as session:
            games = await player.get_games(session)

            if game_id in (game.id for game in games):
                return None

            session.add(player)
            await session.commit()

        return player

    async def change_answer_player(self, game_id: int, vk_user_id: int):
        """Закрепить за игроком право на ответ
        :param game_id: id игры в которой принимается ответ
        :param vk_user_id: vk id пользователя от которого ждем ответ
        :return:
        """
        pass

    async def get_games_by_peer_id(self, peer_id: int) -> Sequence[Game] | None:
        async with self.app.database.session() as session:
            result = await session.execute(
                select(Game)
                .where(Game.conversation_id == peer_id)
                .where(
                    not_(
                        Game.game_stage.in_(
                            [GameStage.WAIT_INIT, GameStage.WAITING_CALLBACK]
                        )
                    )
                )
            )
            games = result.scalars().all()

        return games if games else None

    async def get_game_by_id(self, id_: int):
        async with self.app.database.session() as session:
            game = await session.execute(select(Game).where(Game.id == id_))

        return game.scalar_one_or_none()

    async def change_stage(self):
        pass
