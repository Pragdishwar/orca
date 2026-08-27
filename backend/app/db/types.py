"""Column types that behave identically on PostgreSQL and SQLite.

The demo has to run from a single laptop with no database server, but the
production target is still Postgres. Every model therefore uses these
decorators instead of the postgresql-dialect types directly.
"""
import uuid

from sqlalchemy.types import CHAR, JSON, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB, UUID


class GUID(TypeDecorator):
    """UUID on PostgreSQL, 36-char string elsewhere."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(str(value))
        if dialect.name == "postgresql":
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


# JSONB where available, plain JSON on SQLite.
JSONColumn = JSON().with_variant(JSONB(), "postgresql")
