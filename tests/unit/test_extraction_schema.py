"""Tests for the Pydantic extraction schema (app/schemas/extraction.py)."""

import pytest
from pydantic import ValidationError

from app.schemas.extraction import (
    ExtractedIngredient,
    ExtractedRecipe,
    ExtractedStep,
    SuggestedTag,
)


@pytest.fixture
def valid_ingredient() -> dict:
    """Provide a minimal valid ExtractedIngredient payload."""
    return {
        "group_label": None,
        "quantity": 2.0,
        "quantity_max": None,
        "unit": "Stk",
        "name": "Ei",
        "base_name": "ei",
        "note": None,
    }


@pytest.fixture
def valid_step() -> dict:
    """Provide a minimal valid ExtractedStep payload."""
    return {"group_label": None, "text": "Eier verquirlen."}


@pytest.fixture
def valid_found_recipe(valid_ingredient: dict, valid_step: dict) -> dict:
    """Provide a complete, valid recipe_found=True payload."""
    return {
        "recipe_found": True,
        "title": "Omelett",
        "servings": "2 Portionen",
        "active_time_minutes": 10,
        "total_time_minutes": 10,
        "source_notes": None,
        "subcategory": "Hauptgerichte",
        "tags": ["vegetarisch"],
        "suggested_new_tags": [],
        "ingredients": [valid_ingredient],
        "steps": [valid_step],
    }


# --- ExtractedIngredient ----------------------------------------------------


def test_extracted_ingredient_accepts_minimal_valid_data(
    valid_ingredient: dict,
) -> None:
    """A valid ingredient with all required fields set is accepted."""
    ingredient = ExtractedIngredient(**valid_ingredient)
    assert ingredient.name == "Ei"


def test_extracted_ingredient_allows_missing_optional_fields() -> None:
    """Optional fields (group_label, quantity, quantity_max, unit, note) may be None."""
    ingredient = ExtractedIngredient(
        group_label=None,
        quantity=None,
        quantity_max=None,
        unit=None,
        name="Mehl",
        base_name="mehl",
        note=None,
    )
    assert ingredient.unit is None


def test_extracted_ingredient_strips_name(valid_ingredient: dict) -> None:
    """Leading and trailing whitespace is stripped from name."""
    valid_ingredient["name"] = "  Ei  "
    ingredient = ExtractedIngredient(**valid_ingredient)
    assert ingredient.name == "Ei"


def test_extracted_ingredient_rejects_empty_name(valid_ingredient: dict) -> None:
    """An empty name is rejected."""
    valid_ingredient["name"] = ""
    with pytest.raises(ValidationError):
        ExtractedIngredient(**valid_ingredient)


def test_extracted_ingredient_rejects_whitespace_only_base_name(
    valid_ingredient: dict,
) -> None:
    """A whitespace-only base_name is rejected, not only a fully empty string."""
    valid_ingredient["base_name"] = "   "
    with pytest.raises(ValidationError):
        ExtractedIngredient(**valid_ingredient)


# --- ExtractedStep ------------------------------------------------------------


def test_extracted_step_accepts_valid_text(valid_step: dict) -> None:
    """A step with non-empty text is accepted."""
    step = ExtractedStep(**valid_step)
    assert step.text == "Eier verquirlen."


def test_extracted_step_allows_missing_group_label(valid_step: dict) -> None:
    """group_label is optional and may be None."""
    step = ExtractedStep(**valid_step)
    assert step.group_label is None


def test_extracted_step_rejects_blank_text(valid_step: dict) -> None:
    """Whitespace-only text is rejected."""
    valid_step["text"] = "   "
    with pytest.raises(ValidationError):
        ExtractedStep(**valid_step)


# --- SuggestedTag --------------------------------------------------------------


def test_suggested_tag_accepts_valid_name_and_group() -> None:
    """A suggested tag with a real name and group is accepted."""
    tag = SuggestedTag(name="Herbst", group="Jahreszeit")
    assert tag.name == "Herbst"


def test_suggested_tag_rejects_blank_name() -> None:
    """A suggested tag without a usable name is rejected."""
    with pytest.raises(ValidationError):
        SuggestedTag(name="  ", group="Jahreszeit")


def test_suggested_tag_rejects_blank_group() -> None:
    """A suggested tag without a usable group is rejected."""
    with pytest.raises(ValidationError):
        SuggestedTag(name="Herbst", group="")


# --- ExtractedRecipe: recipe_found = True -------------------------------------


def test_extracted_recipe_accepts_complete_payload(valid_found_recipe: dict) -> None:
    """A fully filled-in recipe_found=True payload is accepted."""
    recipe = ExtractedRecipe(**valid_found_recipe)
    assert recipe.title == "Omelett"


def test_extracted_recipe_accepts_no_tags(valid_found_recipe: dict) -> None:
    """A found recipe may have zero matching existing tags."""
    valid_found_recipe["tags"] = []
    recipe = ExtractedRecipe(**valid_found_recipe)
    assert recipe.tags == []


def test_extracted_recipe_accepts_no_suggested_new_tags(
    valid_found_recipe: dict,
) -> None:
    """A found recipe may have zero suggested new tags."""
    valid_found_recipe["suggested_new_tags"] = []
    recipe = ExtractedRecipe(**valid_found_recipe)
    assert recipe.suggested_new_tags == []


def test_extracted_recipe_rejects_blank_title_when_found(
    valid_found_recipe: dict,
) -> None:
    """An empty title is rejected when recipe_found is true."""
    valid_found_recipe["title"] = ""
    with pytest.raises(ValidationError, match="title"):
        ExtractedRecipe(**valid_found_recipe)


def test_extracted_recipe_rejects_whitespace_only_title_when_found(
    valid_found_recipe: dict,
) -> None:
    """A whitespace-only title is rejected, not only a fully empty string."""
    valid_found_recipe["title"] = "   "
    with pytest.raises(ValidationError, match="title"):
        ExtractedRecipe(**valid_found_recipe)


def test_extracted_recipe_rejects_blank_subcategory_when_found(
    valid_found_recipe: dict,
) -> None:
    """An empty subcategory is rejected when recipe_found is true."""
    valid_found_recipe["subcategory"] = ""
    with pytest.raises(ValidationError, match="subcategory"):
        ExtractedRecipe(**valid_found_recipe)


def test_extracted_recipe_rejects_empty_ingredients_when_found(
    valid_found_recipe: dict,
) -> None:
    """A found recipe must have at least one ingredient."""
    valid_found_recipe["ingredients"] = []
    with pytest.raises(ValidationError, match="ingredients"):
        ExtractedRecipe(**valid_found_recipe)


def test_extracted_recipe_rejects_empty_steps_when_found(
    valid_found_recipe: dict,
) -> None:
    """A found recipe must have at least one step."""
    valid_found_recipe["steps"] = []
    with pytest.raises(ValidationError, match="steps"):
        ExtractedRecipe(**valid_found_recipe)


def test_extracted_recipe_error_lists_every_missing_field(
    valid_found_recipe: dict,
) -> None:
    """All missing required fields are reported together, not just the first one found."""
    valid_found_recipe["title"] = ""
    valid_found_recipe["ingredients"] = []
    with pytest.raises(ValidationError) as exc_info:
        ExtractedRecipe(**valid_found_recipe)
    message = str(exc_info.value)
    assert "title" in message
    assert "ingredients" in message


# --- ExtractedRecipe: recipe_found = False ------------------------------------


def test_extracted_recipe_accepts_everything_empty_when_not_found() -> None:
    """When recipe_found is false, all other fields may be empty."""
    recipe = ExtractedRecipe(
        recipe_found=False,
        title="",
        servings=None,
        active_time_minutes=None,
        total_time_minutes=None,
        source_notes=None,
        subcategory="",
        tags=[],
        suggested_new_tags=[],
        ingredients=[],
        steps=[],
    )
    assert recipe.recipe_found is False


def test_extracted_recipe_ignores_blank_title_when_not_found() -> None:
    """A whitespace-only title is tolerated when recipe_found is false."""
    recipe = ExtractedRecipe(
        recipe_found=False,
        title="   ",
        servings=None,
        active_time_minutes=None,
        total_time_minutes=None,
        source_notes=None,
        subcategory="",
        tags=[],
        suggested_new_tags=[],
        ingredients=[],
        steps=[],
    )
    assert recipe.recipe_found is False


# --- Shape validation (independent of the recipe_found rule) -----------------


def test_extracted_recipe_rejects_missing_recipe_found(
    valid_found_recipe: dict,
) -> None:
    """recipe_found has no default and must always be present."""
    del valid_found_recipe["recipe_found"]
    with pytest.raises(ValidationError):
        ExtractedRecipe(**valid_found_recipe)


def test_extracted_recipe_rejects_incomplete_ingredient_in_list(
    valid_found_recipe: dict,
) -> None:
    """An ingredient missing a required field invalidates the whole payload."""
    valid_found_recipe["ingredients"] = [{"name": "Ei"}]
    with pytest.raises(ValidationError):
        ExtractedRecipe(**valid_found_recipe)


def test_extracted_recipe_rejects_non_numeric_active_time(
    valid_found_recipe: dict,
) -> None:
    """active_time_minutes must be a number, not an arbitrary string."""
    valid_found_recipe["active_time_minutes"] = "zehn Minuten"
    with pytest.raises(ValidationError):
        ExtractedRecipe(**valid_found_recipe)
