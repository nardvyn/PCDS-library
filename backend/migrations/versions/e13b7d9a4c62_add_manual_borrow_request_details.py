"""Add manual book request details and archiveable catalog images

Revision ID: e13b7d9a4c62
Revises: d02a6e4b7c15
Create Date: 2026-09-27
"""
from alembic import op
import sqlalchemy as sa


revision = "e13b7d9a4c62"
down_revision = "d02a6e4b7c15"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("books", schema=None) as batch_op:
        batch_op.add_column(sa.Column("call_number", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("cover_image", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))

    with op.batch_alter_table("borrow_requests", schema=None) as batch_op:
        batch_op.alter_column("book_id", existing_type=sa.Integer(), nullable=True)
        batch_op.add_column(sa.Column("requested_title", sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column("requested_author", sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column("call_number", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("accession_number", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("book_image", sa.String(length=255), nullable=True))
        batch_op.create_index(batch_op.f("ix_borrow_requests_accession_number"), ["accession_number"], unique=False)


def downgrade():
    with op.batch_alter_table("borrow_requests", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_borrow_requests_accession_number"))
        batch_op.drop_column("book_image")
        batch_op.drop_column("accession_number")
        batch_op.drop_column("call_number")
        batch_op.drop_column("requested_author")
        batch_op.drop_column("requested_title")
        batch_op.alter_column("book_id", existing_type=sa.Integer(), nullable=False)
    with op.batch_alter_table("books", schema=None) as batch_op:
        batch_op.drop_column("is_active")
        batch_op.drop_column("cover_image")
        batch_op.drop_column("call_number")