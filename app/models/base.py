"""Shared declarative base for all SQLAlchemy ORM models."""

from enum import Enum as PyEnum

from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base class that all ORM models inherit from."""


def enum_column[EnumT: PyEnum](enum_class: type[EnumT]) -> SQLEnum:
    """Return an Enum column type that stores member values instead of names.

    Args:
        enum_class: The enum to store, e.g. SourceType.

    Returns:
        A SQLAlchemy Enum type storing values such as "link" rather than "LINK".
    """
    return SQLEnum(
        enum_class,
        values_callable=lambda enum_cls: [member.value for member in enum_cls],
    )
