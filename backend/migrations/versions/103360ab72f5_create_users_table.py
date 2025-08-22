"""create_users_table

Revision ID: 103360ab72f5
Revises: 
Create Date: 2025-08-22 02:01:25.806501

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '103360ab72f5'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table with all fields
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(255), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('google_id', sa.String(255), nullable=True),
        sa.Column('google_email', sa.String(255), nullable=True),
        sa.Column('google_name', sa.String(255), nullable=True),
        sa.Column('google_picture', sa.String(500), nullable=True),
        sa.Column('supabase_id', sa.String(255), nullable=True),
        sa.Column('supabase_email', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('auth_method', sa.String(50), default='local'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add unique constraints using batch operations for SQLite
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_users_username', ['username'])
        batch_op.create_unique_constraint('uq_users_email', ['email'])
        batch_op.create_unique_constraint('uq_users_google_id', ['google_id'])
        batch_op.create_unique_constraint('uq_users_google_email', ['google_email'])
        batch_op.create_unique_constraint('uq_users_supabase_id', ['supabase_id'])
        batch_op.create_unique_constraint('uq_users_supabase_email', ['supabase_email'])


def downgrade() -> None:
    # Drop table (constraints will be dropped automatically)
    op.drop_table('users') 