import sys
import os

# Get the absolute path to the directory containing env.py (which is /app/alembic)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Get the parent directory (which should be /app, your project root inside the container)
project_root = os.path.abspath(os.path.join(current_dir, '..'))

# Add the project root to sys.path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy import create_engine # <-- Add this import!

from alembic import context

from backend.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Set the SQLAlchemy URL from environment variable for online migrations
# This will override any sqlalchemy.url in alembic.ini for online mode
# We will use this directly instead of reading from config.ini
# config.set_main_option("sqlalchemy.url", os.environ.get("DATABASE_SQLALCHEMY_URL")) # Option 1: Set into config object (less direct control)


def run_migrations_offline():
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


def run_migrations_online():
    """Run migrations in 'online' mode."""
    # Retrieve the DATABASE_SQLALCHEMY_URL directly from environment variables
    db_url = os.environ.get("DATABASE_SQLALCHEMY_URL")

    if not db_url:
        raise Exception("DATABASE_SQLALCHEMY_URL environment variable is not set!")

    # Pass the URL directly to create_engine, bypassing config.get_section for the URL
    connectable = create_engine(db_url, poolclass=pool.NullPool) # <-- Changed to create_engine and pass db_url directly

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()