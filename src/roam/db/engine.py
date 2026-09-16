from sqlalchemy import create_engine, Engine
from sqlalchemy.ext.asyncio import create_async_engine

from roam.settings import settings

sync_engine: Engine = create_engine(settings.sqlalchemy_url)
async_engine: Engine = create_async_engine(settings.sqlalchemy_url,
                                           pool_size=settings.db_pool_size,
                                           max_overflow=0,
                                           pool_pre_ping=True,
                                           pool_recycle=1800)

def format_vector(values: list[float]) -> str:
    str_values = [ str(vector) for vector in values ]
    vector = ','.join(str_values)
    return '[' + vector + ']'