"""Create books table

Revision ID: b22c9e4f1a30
Revises: a1078d26e395
Create Date: 2026-09-26
"""
from alembic import op
import sqlalchemy as sa


revision = "b22c9e4f1a30"
down_revision = "a1078d26e395"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "books",
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("author", sa.String(length=150), nullable=False),
        sa.Column("isbn", sa.String(length=30), nullable=True),
        sa.Column("accession_number", sa.String(length=50), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column("total_copies", sa.Integer(), nullable=False),
        sa.Column("available_copies", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("book_id"),
        sa.UniqueConstraint("isbn"),
        sa.UniqueConstraint("accession_number"),
    )
    with op.batch_alter_table("books", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_books_title"), ["title"], unique=False)


def downgrade():
    with op.batch_alter_table("books", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_books_title"))
    op.drop_table("books")
