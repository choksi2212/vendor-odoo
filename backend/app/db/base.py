import uuid

from sqlalchemy import String, TypeDecorator
from sqlalchemy.orm import DeclarativeBase


def generate_uuid() -> str:
    """Generate a UUID4 as string for use as default column value."""
    return str(uuid.uuid4())


class GUID(TypeDecorator):
    """Platform-independent UUID type.
    
    Uses String(36) storage to work with both PostgreSQL and SQLite.
    Stores as string in all databases, converts to/from Python str.
    """
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if isinstance(value, uuid.UUID):
                return str(value)
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return str(value)
        return value


class Base(DeclarativeBase):
    pass
