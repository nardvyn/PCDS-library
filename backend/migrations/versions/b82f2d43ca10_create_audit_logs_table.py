"""Create audit logs table

Revision ID: b82f2d43ca10
Revises: a71d5c9e2f04
Create Date: 2026-09-27
"""
from alembic import op
import sqlalchemy as sa


revision = "b82f2d43ca10"
down_revision = "a71d5c9e2f04"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "audit_logs",
        sa.Column("audit_log_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_name", sa.String(length=150), nullable=False),
        sa.Column("actor_role", sa.String(length=30), nullable=False),
        sa.Column("action", sa.String(length=60), nullable=False),
        sa.Column("entity_type", sa.String(length=60), nullable=False),
        sa.Column("entity_id", sa.String(length=80), nullable=True),
        sa.Column("details", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.user_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("audit_log_id"),
    )
    with op.batch_alter_table("audit_logs", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_audit_logs_actor_user_id"), ["actor_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_audit_logs_action"), ["action"], unique=False)
        batch_op.create_index(batch_op.f("ix_audit_logs_created_at"), ["created_at"], unique=False)


def downgrade():
    with op.batch_alter_table("audit_logs", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_audit_logs_created_at"))
        batch_op.drop_index(batch_op.f("ix_audit_logs_action"))
        batch_op.drop_index(batch_op.f("ix_audit_logs_actor_user_id"))
    op.drop_table("audit_logs")