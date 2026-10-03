"""Allow email-first registration

Revision ID: f64b0a8c3d21
Revises: e53a9f7d2c10
Create Date: 2026-09-26
"""
from alembic import op
import sqlalchemy as sa


revision = "f64b0a8c3d21"
down_revision = "e53a9f7d2c10"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column("school_id", existing_type=sa.String(length=50), nullable=True)


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column("school_id", existing_type=sa.String(length=50), nullable=False)