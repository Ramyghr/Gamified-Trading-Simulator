# alembic/env.py
import os
import sys
from logging.config import fileConfig
from dotenv import load_dotenv

from sqlalchemy import engine_from_config, pool
from alembic import context

# -----------------------------
# PATH SETUP
# -----------------------------
# Add app directory to sys.path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# -----------------------------
# LOAD ENV VARIABLES
# -----------------------------
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path) 

# -----------------------------
# ALEMBIC CONFIG
# -----------------------------
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -----------------------------
# IMPORT BASE AND MODELS
# -----------------------------
try:
    # Import from the central models module
    from app.models import Base
    
    # Also import all models to ensure they're registered
    from app.models import *
    
    print("✅ All models imported successfully via app.models")
    target_metadata = Base.metadata
    print(f"✅ Base.metadata configured with {len(Base.metadata.tables)} tables")
    
    # Debug: List all tables
    print("\n📋 Tables found:")
    for table_name in sorted(Base.metadata.tables.keys()):
        print(f"  - {table_name}")

except ImportError as e:
    print(f"❌ Error importing models: {e}")
    import traceback
    traceback.print_exc()
    target_metadata = None

# -----------------------------
# OVERRIDE DATABASE URL
# -----------------------------
database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)
else:
    print("⚠️ DATABASE_URL not found in environment variables")

# -----------------------------
# RUN MIGRATIONS
# -----------------------------
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
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()