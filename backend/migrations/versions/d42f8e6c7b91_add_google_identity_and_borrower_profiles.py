"""Add Google identity and borrower profiles

Revision ID: d42f8e6c7b91
Revises: c31e7a5d9b42
Create Date: 2026-09-26
"""
from alembic import op
import sqlalchemy as sa


revision = "d42f8e6c7b91"
down_revision = "c31e7a5d9b42"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column("password_hash", existing_type=sa.String(length=255), nullable=True)
        batch_op.add_column(sa.Column("google_id", sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column("email", sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column("first_name", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("last_name", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("profile_picture", sa.String(length=500), nullable=True))
        batch_op.create_index(batch_op.f("ix_users_google_id"), ["google_id"], unique=True)
        batch_op.create_index(batch_op.f("ix_users_email"), ["email"], unique=True)

    op.create_table(
        "borrower_profiles",
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("school_id_number", sa.String(length=50), nullable=True),
        sa.Column("course", sa.String(length=100), nullable=True),
        sa.Column("year_level", sa.String(length=30), nullable=True),
        sa.Column("section", sa.String(length=50), nullable=True),
        sa.Column("department", sa.String(length=120), nullable=True),
        sa.Column("contact_number", sa.String(length=20), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("school_id_image", sa.String(length=255), nullable=True),
        sa.Column("verification_status", sa.Enum("PENDING_VERIFICATION", "VERIFIED", "REJECTED", "SUSPENDED", name="verification_statuses"), nullable=False),
        sa.Column("verified_by", sa.Integer(), nullable=True),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["verified_by"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("profile_id"),
        sa.UniqueConstraint("school_id_number"),
        sa.UniqueConstraint("user_id"),
    )


def downgrade():
    op.drop_table("borrower_profiles")
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_users_google_id"))
        batch_op.drop_index(batch_op.f("ix_users_email"))
        batch_op.drop_column("profile_picture")
        batch_op.drop_column("last_name")
        batch_op.drop_column("first_name")
        batch_op.drop_column("email")
        batch_op.drop_column("google_id")
        batch_op.alter_column("password_hash", existing_type=sa.String(length=255), nullable=False)
