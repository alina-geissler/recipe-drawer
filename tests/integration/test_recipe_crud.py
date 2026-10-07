"""Integration tests for recipe CRUD functions."""

from sqlalchemy.orm import Session

from app.core.enums import RecipeStatus, SourceType
from app.crud.recipe import create_recipe, delete_recipe, get_recipe, update_recipe
from app.models import Image, Ingredient, Recipe, Step, Tag, TagGroup


def _make_recipe(**overrides: object) -> Recipe:
    """Build a minimal, valid Recipe instance for use in tests."""
    defaults: dict[str, object] = {
        "title": "Apple Pie",
        "source_type": SourceType.TEXT,
        "status": RecipeStatus.DRAFT,
    }
    defaults.update(overrides)
    return Recipe(**defaults)


def _make_tag(session: Session, name: str = "vegan") -> Tag:
    """Create and flush a tag, along with its own tag group, for use in tests."""
    group = TagGroup(name=f"{name}-group", position=0)
    tag = Tag(name=name, is_pinned=False)
    group.tags.append(tag)
    session.add(group)
    session.flush()
    return tag


def test_create_recipe_persists_recipe_with_ingredients_steps_and_tags(
    db_session: Session,
) -> None:
    """create_recipe stores the recipe together with its ingredients, steps and tags."""
    tag = _make_tag(db_session)
    recipe = _make_recipe(
        ingredients=[
            Ingredient(position=0, name="Eggs", base_name="egg"),
            Ingredient(
                position=1, name="Flour", base_name="flour", quantity=500, unit="g"
            ),
        ],
        steps=[
            Step(position=0, text="Mix the dough."),
            Step(position=1, text="Bake for 40 minutes."),
        ],
        tags=[tag],
    )

    create_recipe(db_session, recipe)
    db_session.expire_all()

    fetched = get_recipe(db_session, recipe.id)
    assert fetched is not None
    assert fetched.title == "Apple Pie"
    assert [ingredient.name for ingredient in fetched.ingredients] == ["Eggs", "Flour"]
    assert [step.text for step in fetched.steps] == [
        "Mix the dough.",
        "Bake for 40 minutes.",
    ]
    assert [t.name for t in fetched.tags] == ["vegan"]


def test_get_recipe_returns_none_for_unknown_id(db_session: Session) -> None:
    """get_recipe returns None when no recipe with the given id exists."""
    assert get_recipe(db_session, 999) is None


def test_update_recipe_replaces_ingredients_steps_and_tags(db_session: Session) -> None:
    """update_recipe fully replaces the ingredient, step and tag collections."""
    old_tag = _make_tag(db_session, name="old-tag")
    new_tag = _make_tag(db_session, name="new-tag")
    recipe = _make_recipe(
        ingredients=[Ingredient(position=0, name="Eggs", base_name="egg")],
        steps=[Step(position=0, text="Mix the dough.")],
        tags=[old_tag],
    )
    create_recipe(db_session, recipe)
    old_ingredient_id = recipe.ingredients[0].id
    old_step_id = recipe.steps[0].id

    update_recipe(
        db_session,
        recipe,
        ingredients=[Ingredient(position=0, name="Sugar", base_name="sugar")],
        steps=[Step(position=0, text="Caramelize the sugar.")],
        tags=[new_tag],
    )
    db_session.expire_all()

    fetched = get_recipe(db_session, recipe.id)
    assert fetched is not None
    assert [ingredient.name for ingredient in fetched.ingredients] == ["Sugar"]
    assert [step.text for step in fetched.steps] == ["Caramelize the sugar."]
    assert [t.name for t in fetched.tags] == ["new-tag"]

    # The old ingredient/step rows are gone (delete-orphan cascade); the old
    # tag row is not, since tags are independent entities, not owned by the recipe.
    assert db_session.get(Ingredient, old_ingredient_id) is None
    assert db_session.get(Step, old_step_id) is None
    assert db_session.get(Tag, old_tag.id) is not None


def test_delete_recipe_cascades_to_ingredients_steps_and_images(
    db_session: Session,
) -> None:
    """Deleting a recipe also removes its ingredients, steps and images.

    This exercises both enforcement layers: the ORM-level `cascade="all,
    delete-orphan"` on the relationships, and the database-level
    `ondelete="CASCADE"` on the foreign keys (only active because the
    db_session fixture enables `PRAGMA foreign_keys=ON`).
    """
    tag = _make_tag(db_session)
    recipe = _make_recipe(
        ingredients=[Ingredient(position=0, name="Eggs", base_name="egg")],
        steps=[Step(position=0, text="Mix the dough.")],
        tags=[tag],
        images=[
            Image(
                position=0,
                file_path="apple-pie.jpg",
                file_hash="a" * 64,
                perceptual_hash="b" * 16,
            )
        ],
    )
    create_recipe(db_session, recipe)
    recipe_id = recipe.id
    ingredient_id = recipe.ingredients[0].id
    step_id = recipe.steps[0].id
    image_id = recipe.images[0].id

    delete_recipe(db_session, recipe)

    assert db_session.get(Recipe, recipe_id) is None
    assert db_session.get(Ingredient, ingredient_id) is None
    assert db_session.get(Step, step_id) is None
    assert db_session.get(Image, image_id) is None
    # The tag itself is an independent entity and must survive the recipe's deletion.
    assert db_session.get(Tag, tag.id) is not None
