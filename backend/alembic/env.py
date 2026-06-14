# alembic/env.py
#
# Alembic uses this file to know:
#   1. Which database to connect to (we read from our .env)
#   2. Which tables exist (we point to our SQLAlchemy Base.metadata)
#
# Alembic uses the SYNC database URL (not async) because it runs
# as a command-line tool, not inside FastAPI's async event loop.

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ── LOAD OUR APP SETTINGS ────────────────────────────────────────
# Import settings so we can read DATABASE_URL from .env
from app.config import settings

# Import Base so Alembic can see all our table definitions.
# As we add model files, we import them here so Alembic detects them.
from app.database import Base

# Import all models so Alembic can detect every table.
# This single import pulls in all 9 model files via models/__init__.py
import app.models  # noqa: F401  (imported for its side effects — registers models with Base)


# ── ALEMBIC CONFIG ───────────────────────────────────────────────
config = context.config

# Set up logging from the alembic.ini file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Tell Alembic about our tables so it can auto-detect schema changes
target_metadata = Base.metadata

# Override the database URL from alembic.ini with our .env value.
# We escape the % character because alembic.ini uses Python's configparser
# which treats % as a special interpolation character.
# The URL 'postgresql://postgres:M%40her@...' has a % that must become %%
escaped_url = settings.DATABASE_URL.replace("%", "%%")
config.set_main_option("sqlalchemy.url", escaped_url)


# ── OFFLINE MODE ─────────────────────────────────────────────────
# Generates SQL scripts without connecting to the database.
# Rarely used — ignore unless you need to review SQL before running.
def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ── ONLINE MODE ──────────────────────────────────────────────────
# Connects to the database and applies migrations directly.
# This is the mode used when you run: uv run alembic upgrade head
def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,    # Don't pool connections during migrations
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


# ── RUN ──────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
