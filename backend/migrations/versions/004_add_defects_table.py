"""Add defects table for defect management

Revision ID: 004
Revises: 003
Create Date: 2025-01-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create defects table with indexes and foreign keys."""
    # Create defects table
    op.create_table(
        'defects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='Open'),
        sa.Column('assigned_to', sa.String(length=255), nullable=True),
        sa.Column('reported_by', sa.String(length=255), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('module_id', sa.String(length=36), nullable=True),
        sa.Column('scenario_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ondelete='SET NULL')
    )
    
    # Create indexes for defects table
    op.create_index('idx_defects_title', 'defects', ['title'], unique=False)
    op.create_index('idx_defects_severity', 'defects', ['severity'], unique=False)
    op.create_index('idx_defects_priority', 'defects', ['priority'], unique=False)
    op.create_index('idx_defects_status', 'defects', ['status'], unique=False)
    op.create_index('idx_defects_assigned_to', 'defects', ['assigned_to'], unique=False)
    op.create_index('idx_defects_project_id', 'defects', ['project_id'], unique=False)
    op.create_index('idx_defects_module_id', 'defects', ['module_id'], unique=False)
    op.create_index('idx_defects_scenario_id', 'defects', ['scenario_id'], unique=False)
    op.create_index('idx_defects_created_at', 'defects', ['created_at'], unique=False)
    
    # Create composite indexes for common query patterns
    op.create_index('idx_defects_project_status', 'defects', ['project_id', 'status'], unique=False)
    op.create_index('idx_defects_project_severity', 'defects', ['project_id', 'severity'], unique=False)


def downgrade() -> None:
    """Drop defects table and indexes."""
    # Drop composite indexes
    op.drop_index('idx_defects_project_severity', table_name='defects')
    op.drop_index('idx_defects_project_status', table_name='defects')
    
    # Drop single column indexes
    op.drop_index('idx_defects_created_at', table_name='defects')
    op.drop_index('idx_defects_scenario_id', table_name='defects')
    op.drop_index('idx_defects_module_id', table_name='defects')
    op.drop_index('idx_defects_project_id', table_name='defects')
    op.drop_index('idx_defects_assigned_to', table_name='defects')
    op.drop_index('idx_defects_status', table_name='defects')
    op.drop_index('idx_defects_priority', table_name='defects')
    op.drop_index('idx_defects_severity', table_name='defects')
    op.drop_index('idx_defects_title', table_name='defects')
    
    # Drop table
    op.drop_table('defects')
