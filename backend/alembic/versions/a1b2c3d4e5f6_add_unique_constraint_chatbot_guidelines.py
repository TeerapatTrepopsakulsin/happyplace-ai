"""add_unique_constraint_chatbot_guidelines

Revision ID: a1b2c3d4e5f6
Revises: 9605741b4f35
Create Date: 2026-04-02 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '9605741b4f35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(
        'uq_chatbot_guidelines_user_id',
        'chatbot_guidelines',
        ['user_id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_chatbot_guidelines_user_id', 'chatbot_guidelines', type_='unique')
