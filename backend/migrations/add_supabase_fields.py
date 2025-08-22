"""Add Supabase fields to users table

Revision ID: add_supabase_fields
Revises: add_missing_google_oauth_fields
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_supabase_fields'
down_revision = 'add_missing_google_oauth_fields'
branch_labels = None
depends_on = None

def upgrade():
    # Add Supabase fields to users table
    op.add_column('users', sa.Column('supabase_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('supabase_email', sa.String(255), nullable=True))
    
    # Create unique indexes for Supabase fields
    op.create_unique_constraint('uq_users_supabase_id', 'users', ['supabase_id'])
    op.create_unique_constraint('uq_users_supabase_email', 'users', ['supabase_email'])

def downgrade():
    # Remove unique constraints
    op.drop_constraint('uq_users_supabase_id', 'users', type_='unique')
    op.drop_constraint('uq_users_supabase_email', 'users', type_='unique')
    
    # Remove Supabase fields
    op.drop_column('users', 'supabase_email')
    op.drop_column('users', 'supabase_id')
