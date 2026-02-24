from __future__ import with_statement

from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config, pool

from alembic import context

# Alembic config object (อ่านค่าจาก alembic.ini)
config = context.config

# ตั้งค่า logging ตาม alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- IMPORTANT: import Base + models so Alembic can "see" tables ---
from app.db.base import Base # noqa: E402
import app.models  # noqa: F401, E402 (imports User/Voucher/Balance/LedgerEvent via __init__.py)

target_metadata = Base.metadata

def _set_sqlalchemy_url_from_env() -> None:
    """
    Use DATABASE_URL from environment (provided by docker compose env_file).
    This avoids hardcoding credentials in alembic.ini
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set. Check backend/.env and docker compose env_file.")
    config.set_main_option("sqlalchemy.url", db_url)

def run_migrations_offline() -> None:
    _set_sqlalchemy_url_from_env()  # Set DB URL before configuring context
   
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,  # Detect column type changes
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    _set_sqlalchemy_url_from_env()  # Set DB URL before creating engine
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            compare_type=True  # Detect column type changes
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
