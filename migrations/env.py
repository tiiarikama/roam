import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from roam.db.tables import metadata
from roam.settings import settings

# Alembic Config object, provides access to the values within the .ini file in use.
config = context.config
config.set_main_option("sqlalchemy.url", settings.sqlalchemy_url.replace("%", "%%"))

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

INGESTION_TABLES = {"parks", "park_chunks"}

def include_object(object_, name, type_, reflected, compare_to) -> bool:
    if type_ == "table" and name in INGESTION_TABLES:
        return False
    elif type_ == "index" and object_.table.name in INGESTION_TABLES:
        return False
    else:
        return True

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL
    and not an Engine. By skipping the Engine creation
    DBAPI does not need to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection,
                      target_metadata=target_metadata,
                      include_object=include_object,
                    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

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
