"""empty message

Revision ID: f69fd6f5a702
Revises: 0c0d63c7f6c9
Create Date: 2021-03-28 00:25:11.295059

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f69fd6f5a702'
down_revision = '0c0d63c7f6c9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('avatar_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'user', 'file', ['avatar_id'], ['id'])
    op.drop_column('user', 'avatar')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('avatar', sa.INTEGER(), nullable=True))
    op.drop_constraint(None, 'user', type_='foreignkey')
    op.drop_column('user', 'avatar_id')
    # ### end Alembic commands ###
