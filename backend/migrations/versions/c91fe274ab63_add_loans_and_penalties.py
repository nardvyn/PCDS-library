"""Add loans and penalties

Revision ID: c91fe274ab63
Revises: b82f2d43ca10
Create Date: 2026-09-27
"""
from alembic import op
import sqlalchemy as sa


revision = "c91fe274ab63"
down_revision = "b82f2d43ca10"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "loans",
        sa.Column("loan_id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("borrowed_at", sa.DateTime(), nullable=False),
        sa.Column("due_date", sa.DateTime(), nullable=False),
        sa.Column("returned_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.Enum("ACTIVE", "RETURNED", "LOST", name="loan_statuses"), nullable=False),
        sa.Column("return_condition", sa.Enum("GOOD", "DAMAGED", "LOST", name="return_conditions"), nullable=True),
        sa.ForeignKeyConstraint(["request_id"], ["borrow_requests.request_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["book_id"], ["books.book_id"]),
        sa.PrimaryKeyConstraint("loan_id"),
        sa.UniqueConstraint("request_id"),
    )
    with op.batch_alter_table("loans", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_loans_user_id"), ["user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_loans_book_id"), ["book_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_loans_status"), ["status"], unique=False)

    op.create_table(
        "penalties",
        sa.Column("penalty_id", sa.Integer(), nullable=False),
        sa.Column("loan_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("late_days", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("UNPAID", "PAID", name="penalty_statuses"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["loan_id"], ["loans.loan_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("penalty_id"),
        sa.UniqueConstraint("loan_id"),
    )
    with op.batch_alter_table("penalties", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_penalties_user_id"), ["user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_penalties_status"), ["status"], unique=False)


def downgrade():
    with op.batch_alter_table("penalties", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_penalties_status"))
        batch_op.drop_index(batch_op.f("ix_penalties_user_id"))
    op.drop_table("penalties")
    with op.batch_alter_table("loans", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_loans_status"))
        batch_op.drop_index(batch_op.f("ix_loans_book_id"))
        batch_op.drop_index(batch_op.f("ix_loans_user_id"))
    op.drop_table("loans")
