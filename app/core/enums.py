"""Enumerations shared across models, services and the import pipeline."""

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


class FetchFailureReason(StrEnum):
    """Why a recipe page could not be fetched; each reason has its own user reaction.

    The mapping from error cases to reasons and reactions is described in plan section 7.3.
    """

    INVALID_URL = "invalid_url"
    HOST_NOT_FOUND = "host_not_found"
    LOCAL_ADDRESS = "local_address"
    BLOCKED = "blocked"
    PAGE_NOT_FOUND = "page_not_found"
    TEMPORARY_FAILURE = "temporary_failure"
