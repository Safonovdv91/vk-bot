"""add constraint table question-game-player

Revision ID: 9966e06abd47
Revises: 76674edd5a4f
Create Date: 2024-12-28 12:28:15.231664

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9966e06abd47'
down_revision: Union[str, None] = '76674edd5a4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('blitz_player_question_games',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.Integer(), nullable=False),
    sa.Column('game_id', sa.Integer(), nullable=False),
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['game_id'], ['blitz_games.id'], ),
    sa.ForeignKeyConstraint(['player_id'], ['blitz_players.id'], ),
    sa.ForeignKeyConstraint(['question_id'], ['blitz_questions.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('player_id', 'game_id', 'question_id', name='idx_unique_blitz_player_game_question')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('blitz_player_question_games')
    # ### end Alembic commands ###
