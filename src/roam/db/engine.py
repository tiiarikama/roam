from sqlalchemy import create_engine, Engine

from roam.settings import settings

sync_engine: Engine = create_engine(settings.sqlalchemy_url)

def format_vector(values: list[float]) -> str:
    str_values = [ str(vector) for vector in values ]
    vector = ','.join(str_values)
    return '[' + vector + ']'