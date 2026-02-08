from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self, database_url: str) -> None:
        self.engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            future=True,
        )
        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    def init_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    def session(self) -> Generator[Session, None, None]:
        session = self.session_factory()
        try:
            yield session
        finally:
            session.close()
