"""Pydantic schema for the structured recipe extraction returned by the LLM."""

from typing import Annotated

from pydantic import BaseModel, StringConstraints, model_validator

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class SuggestedTag(BaseModel):
    """A new tag suggested by the LLM, to be confirmed before it is created."""

    name: NonEmptyStr
    group: NonEmptyStr


class ExtractedIngredient(BaseModel):
    """One ingredient line as returned by the LLM, before it becomes an Ingredient row."""

    group_label: str | None
    quantity: float | None
    quantity_max: float | None
    unit: str | None
    name: NonEmptyStr
    base_name: NonEmptyStr
    note: str | None


class ExtractedStep(BaseModel):
    """One instruction step as returned by the LLM, before it becomes a Step row."""

    group_label: str | None
    text: NonEmptyStr


class ExtractedRecipe(BaseModel):
    """The full structured result the LLM returns for one recipe extraction request."""

    recipe_found: bool
    title: str
    servings: str | None
    active_time_minutes: int | None
    total_time_minutes: int | None
    source_notes: str | None
    subcategory: str
    tags: list[str]
    suggested_new_tags: list[SuggestedTag]
    ingredients: list[ExtractedIngredient]
    steps: list[ExtractedStep]

    @model_validator(mode="after")
    def validate_required_when_found(self) -> ExtractedRecipe:
        """Reject the payload if recipe_found is true but required fields are missing."""
        if self.recipe_found:
            missing = []
            if not self.title.strip():
                missing.append("title")
            if not self.subcategory.strip():
                missing.append("subcategory")
            if not self.ingredients:
                missing.append("ingredients")
            if not self.steps:
                missing.append("steps")
            if missing:
                raise ValueError(f"Missing required field(s): {', '.join(missing)}")
        return self
