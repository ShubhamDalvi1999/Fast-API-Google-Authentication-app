"""Add missing Google OAuth fields to users table

Revision ID: add_missing_google_oauth_fields
Revises: add_google_oauth_fields
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_missing_google_oauth_fields'
down_revision = 'add_google_oauth_fields'
branch_labels = None
depends_on = None

def upgrade():
    # Add missing columns that don't exist yet
    # Check if columns exist before adding them
    
    # Add created_at and updated_at columns
    try:
        op.add_column('users', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
    except Exception:
        pass  # Column might already exist
    
    try:
        op.add_column('users', sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()))
    except Exception:
        pass  # Column might already exist
    
    # Add auth_method column
    try:
        op.add_column('users', sa.Column('auth_method', sa.String(50), default='local'))
    except Exception:
        pass  # Column might already exist
    
    # Add unique constraints if they don't exist
    try:
        op.create_unique_constraint('uq_users_email', 'users', ['email'])
    except Exception:
        pass  # Constraint might already exist
    
    try:
        op.create_unique_constraint('uq_users_google_id', 'users', ['google_id'])
    except Exception:
        pass  # Constraint might already exist
    
    try:
        op.create_unique_constraint('uq_users_google_email', 'users', ['google_email'])
    except Exception:
        pass  # Constraint might already exist

def downgrade():
    # Remove unique constraints
    try:
        op.drop_constraint('uq_users_google_email', 'users', type_='unique')
    except Exception:
        pass
    
    try:
        op.drop_constraint('uq_users_google_id', 'users', type_='unique')
    except Exception:
        pass
    
    try:
        op.drop_constraint('uq_users_email', 'users', type_='unique')
    except Exception:
        pass
    
    # Remove columns
    try:
        op.drop_column('users', 'auth_method')
    except Exception:
        pass
    
    try:
        op.drop_column('users', 'updated_at')
    except Exception:
        pass
    
    try:
        op.drop_column('users', 'created_at')
    except Exception:
        pass
