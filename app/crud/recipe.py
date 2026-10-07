"""CRUD functions for recipes, including their ingredients, steps and tags."""

from sqlalchemy.orm import Session

from app.models import Ingredient, Recipe, Step, Tag


def create_recipe(session: Session, recipe: Recipe) -> Recipe:
    """Persist a new recipe, including any ingredients, steps and tags already set on it.

    Args:
        session: An open SQLAlchemy session; the caller is responsible for committing.
        recipe: A Recipe instance with its fields (and optionally ingredients, steps
            and tags) already set, not yet added to the session.

    Returns:
        The same Recipe instance, with its id and server-generated defaults populated.
    """
    session.add(recipe)
    session.flush()
    return recipe


def get_recipe(session: Session, recipe_id: int) -> Recipe | None:
    """Fetch a recipe by id.

    Args:
        session: An open SQLAlchemy session.
        recipe_id: The id of the recipe to fetch.

    Returns:
        The matching Recipe instance, or None if no recipe with that id exists.
    """
    return session.get(Recipe, recipe_id)


def update_recipe(
    session: Session,
    recipe: Recipe,
    ingredients: list[Ingredient],
    steps: list[Step],
    tags: list[Tag],
) -> Recipe:
    """Replace a recipe's ingredients, steps and tags with the given lists.

    Scalar fields (title, servings, etc.) are expected to already be set on
    `recipe` by the caller before this is called. The existing ingredient and
    step rows are fully replaced (removed via cascade, not merged by id); tag
    links are replaced without affecting the Tag rows themselves.

    Args:
        session: An open SQLAlchemy session; the caller is responsible for committing.
        recipe: The recipe to update, already attached to the session.
        ingredients: The full new list of ingredients, in display order.
        steps: The full new list of steps, in display order.
        tags: The full new list of tags to link to the recipe.

    Returns:
        The same Recipe instance.
    """
    recipe.ingredients = ingredients
    recipe.steps = steps
    recipe.tags = tags
    session.flush()
    return recipe


def delete_recipe(session: Session, recipe: Recipe) -> None:
    """Delete a recipe, cascading to its ingredients, steps and images.

    Args:
        session: An open SQLAlchemy session; the caller is responsible for committing.
        recipe: The recipe to delete, already attached to the session.
    """
    session.delete(recipe)
    session.flush()
