"""Add no database columns; keeps the upload migration marker.

Revision ID: e53a9f7d2c10
Revises: d42f8e6c7b91
Create Date: 2026-09-26
"""
from alembic import op


revision = "e53a9f7d2c10"
down_revision = "d42f8e6c7b91"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass