"""Add reports and scenarios tables for test execution data

Revision ID: 003
Revises: 002
Create Date: 2025-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create reports and scenarios tables with indexes."""
    # Create reports table
    op.create_table(
        'reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('module_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('total_scenarios', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('passed_scenarios', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_scenarios', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('skipped_scenarios', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('uploaded_by', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ondelete='CASCADE')
    )
    
    # Create indexes for reports table
    op.create_index('idx_reports_project_id', 'reports', ['project_id'], unique=False)
    op.create_index('idx_reports_module_id', 'reports', ['module_id'], unique=False)
    op.create_index('idx_reports_created_at', 'reports', ['created_at'], unique=False)
    
    # Create scenarios table
    op.create_table(
        'scenarios',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('tags', sa.String(length=500), nullable=True),
        sa.Column('feature', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE')
    )
    
    # Create indexes for scenarios table
    op.create_index('idx_scenarios_report_id', 'scenarios', ['report_id'], unique=False)
    op.create_index('idx_scenarios_status', 'scenarios', ['status'], unique=False)


def downgrade() -> None:
    """Drop scenarios and reports tables with indexes."""
    # Drop scenarios table indexes
    op.drop_index('idx_scenarios_status', table_name='scenarios')
    op.drop_index('idx_scenarios_report_id', table_name='scenarios')
    
    # Drop scenarios table
    op.drop_table('scenarios')
    
    # Drop reports table indexes
    op.drop_index('idx_reports_created_at', table_name='reports')
    op.drop_index('idx_reports_module_id', table_name='reports')
    op.drop_index('idx_reports_project_id', table_name='reports')
    
    # Drop reports table
    op.drop_table('reports')
