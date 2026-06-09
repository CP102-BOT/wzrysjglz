# Alembic environment configuration
import asyncio
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import models
from database import Base
from models import PvPGuide, PvEGuide, CodeItem, QuickRef

# Load .env
from dotenv import load_dotenv
import os
load_dotenv(Path(__file__).parent.parent / ".env")

config = context.config

# Set sqlalchemy.url from environment
db_url = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///data/data.db")
config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

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


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
