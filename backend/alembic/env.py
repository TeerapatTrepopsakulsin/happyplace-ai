import asyncio
import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.models.base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Load database URL from .env and/or environment
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required in environment for Alembic migrations")

# Ensure the config URL reflects this value
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# import models to register metadata
import app.models.users  # noqa: F401
import app.models.invitations  # noqa: F401
import app.models.chat_sessions  # noqa: F401
import app.models.messages  # noqa: F401
import app.models.emotion_snapshots  # noqa: F401
import app.models.chatbot_guidelines  # noqa: F401
import app.models.dashboard_summary  # noqa: F401
import app.models.danger_alerts  # noqa: F401

# set target metadata for 'autogenerate'
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=AsyncAdaptedQueuePool,
        future=True,
        echo=False,
    )

    def do_run_migrations(connection):
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

    async def run_async():
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

    asyncio.run(run_async())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
