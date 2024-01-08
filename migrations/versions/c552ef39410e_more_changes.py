"""More changes

Revision ID: c552ef39410e
Revises: b1dde34626f9
Create Date: 2024-01-07 22:15:46.834273

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c552ef39410e'
down_revision = 'b1dde34626f9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('can_create_calendar_events', sa.Boolean(), nullable=False))
        batch_op.drop_column('canCreateEvents')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('canCreateEvents', sa.BOOLEAN(), nullable=False))
        batch_op.drop_column('can_create_calendar_events')

    # ### end Alembic commands ###
