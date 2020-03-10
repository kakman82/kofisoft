"""empty message

Revision ID: 304cf55d7cb1
Revises: f0a8818e256c
Create Date: 2019-10-14 01:40:56.058436

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '304cf55d7cb1'
down_revision = 'f0a8818e256c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('appointment', sa.Column('type', sa.String(length=50), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('appointment', 'type')
    # ### end Alembic commands ###
