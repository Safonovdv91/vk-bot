"""add vk_messages

Revision ID: 2d783bbcfaf0
Revises: 9966e06abd47
Create Date: 2025-01-05 15:22:30.426859

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2d783bbcfaf0'
down_revision: Union[str, None] = '9966e06abd47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('vk_messages',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('conversation_id', sa.Integer(), nullable=False),
    sa.Column('text', sa.String(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('vk_messages')
    # ### end Alembic commands ###
