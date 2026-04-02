"""add_unique_constraint_dashboard_summary

Revision ID: 9605741b4f35
Revises: 6c6758379380
Create Date: 2026-03-28 17:08:58.752782

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9605741b4f35'
down_revision: Union[str, Sequence[str], None] = '6c6758379380'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(
        'uq_dashboard_summary_user_date',
        'dashboard_summary',
        ['user_id', 'summary_date']
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_dashboard_summary_user_date', 'dashboard_summary', type_='unique')
