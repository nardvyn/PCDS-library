"""Create shared library settings

Revision ID: d02a6e4b7c15
Revises: c91fe274ab63
Create Date: 2026-09-27
"""
from alembic import op
import sqlalchemy as sa


revision = "d02a6e4b7c15"
down_revision = "c91fe274ab63"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "library_settings",
        sa.Column("setting_key", sa.String(length=80), nullable=False),
        sa.Column("setting_value", sa.String(length=120), nullable=False),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["updated_by"], ["users.user_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("setting_key"),
    )


def downgrade():
    op.drop_table("library_settings")
