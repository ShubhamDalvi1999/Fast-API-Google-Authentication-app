"""Add Google OAuth fields to users table

Revision ID: add_google_oauth_fields
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_google_oauth_fields'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to users table
    op.add_column('users', sa.Column('email', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('google_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('google_email', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('google_name', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('google_picture', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.add_column('users', sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()))
    op.add_column('users', sa.Column('auth_method', sa.String(50), default='local'))
    
    # Make existing columns nullable
    op.alter_column('users', 'username', nullable=True)
    op.alter_column('users', 'hashed_password', nullable=True)
    
    # Add unique constraints
    op.create_unique_constraint('uq_users_email', 'users', ['email'])
    op.create_unique_constraint('uq_users_google_id', 'users', ['google_id'])
    op.create_unique_constraint('uq_users_google_email', 'users', ['google_email'])

def downgrade():
    # Remove unique constraints
    op.drop_constraint('uq_users_google_email', 'users', type_='unique')
    op.drop_constraint('uq_users_google_id', 'users', type_='unique')
    op.drop_constraint('uq_users_email', 'users', type_='unique')
    
    # Remove columns
    op.drop_column('users', 'auth_method')
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'created_at')
    op.drop_column('users', 'google_picture')
    op.drop_column('users', 'google_name')
    op.drop_column('users', 'google_email')
    op.drop_column('users', 'google_id')
    op.drop_column('users', 'email')
    
    # Make columns non-nullable again
    op.alter_column('users', 'hashed_password', nullable=False)
    op.alter_column('users', 'username', nullable=False)
