"""Add profile picture column to User model

Revision ID: 09219d8dbb19
Revises: 3530c9148dec
Create Date: 2024-06-06 17:12:27.700896

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '09219d8dbb19'
down_revision = '3530c9148dec'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('profile_picture', sa.String(length=150), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'profile_picture')
    # ### end Alembic commands ###
