"""
Alembic Environment Configuration for JournaBuddy.
Reads DATABASE_URL from environment and runs migrations synchronously
using psycopg2 (Alembic does not support asyncpg directly).
"""
import os
import re
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Load Alembic ini file config
config = context.config

# Setup Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models so Alembic can detect them for autogenerate
from app.models.models import Base  # noqa: F401
target_metadata = Base.metadata


def get_sync_url() -> str:
    """
    Convert asyncpg DATABASE_URL to a psycopg2-compatible synchronous URL.
    Alembic's CLI tooling cannot use asyncpg, so we swap the driver.
    e.g., postgresql+asyncpg://... → postgresql+psycopg2://...
    """
    url = os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
    # Replace asyncpg driver with psycopg2 for synchronous Alembic migrations
    url = re.sub(r"postgresql\+asyncpg", "postgresql+psycopg2", url)
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL without a live connection)."""
    url = get_sync_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (applies directly to the database)."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_sync_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
