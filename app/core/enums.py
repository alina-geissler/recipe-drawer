"""Enumerations shared across SQLAlchemy models."""

from enum import StrEnum


class SourceType(StrEnum):
    """How a recipe was imported: link, image or pasted text."""

    LINK = "link"
    IMAGE = "image"
    TEXT = "text"


class RecipeStatus(StrEnum):
    """Review status of a recipe."""

    DRAFT = "draft"
    SAVED = "saved"
