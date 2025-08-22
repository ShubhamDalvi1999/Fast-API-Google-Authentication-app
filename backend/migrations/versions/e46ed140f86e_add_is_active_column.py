"""add_is_active_column

Revision ID: e46ed140f86e
Revises: 103360ab72f5
Create Date: 2025-08-22 02:07:07.435973

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e46ed140f86e'
down_revision = '103360ab72f5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_active column to users table
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=True, default=True))


def downgrade() -> None:
    # Remove is_active column
    op.drop_column('users', 'is_active') 