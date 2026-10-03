"""Create borrow requests table

Revision ID: c31e7a5d9b42
Revises: b22c9e4f1a30
Create Date: 2026-09-26
"""
from alembic import op
import sqlalchemy as sa


revision = "c31e7a5d9b42"
down_revision = "b22c9e4f1a30"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "borrow_requests",
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "APPROVED", "REJECTED", name="borrow_request_statuses"), nullable=False),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["book_id"], ["books.book_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("request_id"),
    )
    with op.batch_alter_table("borrow_requests", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_borrow_requests_user_id"), ["user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_borrow_requests_book_id"), ["book_id"], unique=False)


def downgrade():
    with op.batch_alter_table("borrow_requests", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_borrow_requests_user_id"))
        batch_op.drop_index(batch_op.f("ix_borrow_requests_book_id"))
    op.drop_table("borrow_requests")
