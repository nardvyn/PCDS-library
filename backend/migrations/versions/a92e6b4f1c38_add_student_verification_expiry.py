"""add student verification expiry

Revision ID: a92e6b4f1c38
Revises: f64b0a8c3d21
"""

from alembic import op
import sqlalchemy as sa


revision = "a92e6b4f1c38"
down_revision = "f64b0a8c3d21"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("borrower_profiles") as batch_op:
        batch_op.add_column(sa.Column("verification_expires_at", sa.DateTime(), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE borrower_profiles bp
            JOIN users u ON u.user_id = bp.user_id
            SET bp.verification_expires_at = DATE_ADD(COALESCE(bp.verified_at, bp.updated_at, bp.created_at), INTERVAL 365 DAY)
            WHERE u.role = 'STUDENT' AND bp.verification_status = 'VERIFIED'
            """
        )
    )


def downgrade():
    with op.batch_alter_table("borrower_profiles") as batch_op:
        batch_op.drop_column("verification_expires_at")
