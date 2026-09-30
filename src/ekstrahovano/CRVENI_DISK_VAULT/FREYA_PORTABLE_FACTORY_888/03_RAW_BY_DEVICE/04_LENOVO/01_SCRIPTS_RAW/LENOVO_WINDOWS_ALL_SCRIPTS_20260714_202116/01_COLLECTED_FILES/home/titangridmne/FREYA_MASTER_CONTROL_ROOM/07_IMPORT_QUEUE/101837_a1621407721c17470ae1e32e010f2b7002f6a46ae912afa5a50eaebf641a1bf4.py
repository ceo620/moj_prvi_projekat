"""init

Revision ID: 20260313_0001
Revises: 
Create Date: 2026-03-13 21:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260313_0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    expense_type_enum = postgresql.ENUM('CAPEX', 'OPEX', name='expense_type_enum')
    milestone_status_enum = postgresql.ENUM('PENDING', 'IN_PROGRESS', 'COMPLETED', 'DELAYED', name='milestone_status_enum')
    audit_action_enum = postgresql.ENUM('INSERT', 'UPDATE', 'DELETE', name='audit_action_enum')
    expense_type_enum.create(op.get_bind(), checkfirst=True)
    milestone_status_enum.create(op.get_bind(), checkfirst=True)
    audit_action_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'project',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('budget', sa.Numeric(18, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('budget > 0', name='ck_project_budget_positive'),
    )
    op.create_index('ix_project_name', 'project', ['name'])

    op.create_table(
        'expense',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('type', expense_type_enum, nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('project.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('amount > 0', name='ck_expense_amount_positive'),
    )
    op.create_index('ix_expense_project_id', 'expense', ['project_id'])

    op.create_table(
        'milestone',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=300), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', milestone_status_enum, nullable=False),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('project.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_milestone_project_id', 'milestone', ['project_id'])

    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('table_name', sa.String(length=100), nullable=False),
        sa.Column('record_id', sa.Integer(), nullable=False),
        sa.Column('action', audit_action_enum, nullable=False),
        sa.Column('changed_by', sa.String(length=150), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('before_data', sa.JSON(), nullable=True),
        sa.Column('after_data', sa.JSON(), nullable=True),
    )
    op.create_index('ix_audit_log_table_name', 'audit_log', ['table_name'])
    op.create_index('ix_audit_log_record_id', 'audit_log', ['record_id'])


def downgrade() -> None:
    op.drop_index('ix_audit_log_record_id', table_name='audit_log')
    op.drop_index('ix_audit_log_table_name', table_name='audit_log')
    op.drop_table('audit_log')
    op.drop_index('ix_milestone_project_id', table_name='milestone')
    op.drop_table('milestone')
    op.drop_index('ix_expense_project_id', table_name='expense')
    op.drop_table('expense')
    op.drop_index('ix_project_name', table_name='project')
    op.drop_table('project')
    postgresql.ENUM(name='audit_action_enum').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='milestone_status_enum').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='expense_type_enum').drop(op.get_bind(), checkfirst=True)
