from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from . import Base
import sys

def build_engine(db_url, connection_pool_size = 10):
    return create_engine(db_url, pool_size=connection_pool_size)

def build_session(engine):
    Session = sessionmaker(engine)
    return Session()

def build_bulk_session(engine):
    Session = sessionmaker(autocommit = False, autoflush = False, bind = engine)
    return Session()

@contextmanager
def build_connection(db_url, connection_pool_size = 10):
    engine = build_engine(db_url, connection_pool_size)
    session = build_session(engine)

    try:
        yield session
    finally:
        session.close()

@contextmanager
def build_bulk_connection(db_url, connection_pool_size = 10):
    engine = build_engine(db_url, connection_pool_size)
    session = build_bulk_session(engine)

    try:
        yield session
    finally:
        session.close()

def build_tables(engine):
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        db_url = str(sys.argv[-1])
    else:
        print(f'No database URL provided. Usage: python -m answer_gen.storage.db [db_url]')
        sys.exit(1)

    engine = build_engine(db_url)
    print(f'Writing tables to Database at {db_url}')
    build_tables(engine)
