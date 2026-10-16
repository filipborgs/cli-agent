from sqlalchemy import Engine
from sqlalchemy import create_engine as sqlalchemy_create_engine


def create_engine(database_url: str) -> Engine:
    return sqlalchemy_create_engine(database_url, pool_pre_ping=True)
