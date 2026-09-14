"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2025-01-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### Create projects table ###
    op.create_table(
        'projects',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('repository_url', sa.String(length=500), nullable=True),
        sa.Column('owner', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create indexes for projects table
    op.create_index('idx_projects_name', 'projects', ['name'], unique=False)
    op.create_index('idx_projects_owner', 'projects', ['owner'], unique=False)
    
    # ### Create modules table ###
    op.create_table(
        'modules',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for modules table
    op.create_index('idx_modules_project_id', 'modules', ['project_id'], unique=False)
    op.create_index('idx_modules_project_name', 'modules', ['project_id', 'name'], unique=True)
    
    # ### Create executions table ###
    op.create_table(
        'executions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('module_id', sa.String(length=36), nullable=False),
        sa.Column('passed', sa.Integer(), nullable=True),
        sa.Column('failed', sa.Integer(), nullable=True),
        sa.Column('total', sa.Integer(), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for executions table
    op.create_index('idx_executions_module_id', 'executions', ['module_id'], unique=False)
    op.create_index('idx_executions_created_at', 'executions', [sa.text('created_at DESC')], unique=False)
    
    # ### Create scenarios table ###
    op.create_table(
        'scenarios',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('execution_id', sa.String(length=36), nullable=False),
        sa.Column('scenario', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('failed_step', sa.String(length=255), nullable=True),
        sa.Column('error', sa.String(), nullable=True),
        sa.Column('attachments', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['execution_id'], ['executions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for scenarios table
    op.create_index('idx_scenarios_execution_id', 'scenarios', ['execution_id'], unique=False)
    op.create_index('idx_scenarios_status', 'scenarios', ['status'], unique=False)
    
    # Create full-text search index on scenarios.error using GIN
    # This index enables efficient full-text search on error messages
    op.execute(
        "CREATE INDEX idx_scenarios_error_fulltext ON scenarios "
        "USING gin(to_tsvector('english', COALESCE(error, '')))"
    )


def downgrade() -> None:
    # Drop full-text search index
    op.execute('DROP INDEX IF EXISTS idx_scenarios_error_fulltext')
    
    # Drop scenarios table and its indexes
    op.drop_index('idx_scenarios_status', table_name='scenarios')
    op.drop_index('idx_scenarios_execution_id', table_name='scenarios')
    op.drop_table('scenarios')
    
    # Drop executions table and its indexes
    op.drop_index('idx_executions_created_at', table_name='executions')
    op.drop_index('idx_executions_module_id', table_name='executions')
    op.drop_table('executions')
    
    # Drop modules table and its indexes
    op.drop_index('idx_modules_project_name', table_name='modules')
    op.drop_index('idx_modules_project_id', table_name='modules')
    op.drop_table('modules')
    
    # Drop projects table and its indexes
    op.drop_index('idx_projects_owner', table_name='projects')
    op.drop_index('idx_projects_name', table_name='projects')
    op.drop_table('projects')
