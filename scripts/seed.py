"""Load seed data (categories, tag groups, tags) into an otherwise empty database.

Renaming or removing an entry in the seed files has no effect on rows that were
already created from an earlier version; the loader only adds what is missing.
"""

from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Category, Tag, TagGroup

SEEDS_DIR = Path(__file__).resolve().parent.parent / "seeds"


def seed_tags(session: Session) -> None:
    """Load tag groups and their tags from seeds/tags.yaml.

    Existing tag groups and tags (matched by name) are left untouched; only
    missing ones are added.

    Args:
        session: An open SQLAlchemy session; the caller is responsible for committing.
    """
    tag_groups_data = yaml.safe_load(
        (SEEDS_DIR / "tags.yaml").read_text(encoding="utf-8")
    )

    for position, group_data in enumerate(tag_groups_data):
        group = session.scalars(
            select(TagGroup).where(TagGroup.name == group_data["name"])
        ).first()
        if group is None:
            group = TagGroup(name=group_data["name"], position=position)
            session.add(group)

        existing_tag_names = {tag.name for tag in group.tags}
        for tag_data in group_data["tags"]:
            if tag_data["name"] not in existing_tag_names:
                group.tags.append(
                    Tag(name=tag_data["name"], is_pinned=tag_data["is_pinned"])
                )


def seed_categories(session: Session) -> None:
    """Load main categories and their subcategories from seeds/categories.yaml.

    Existing categories (matched by name within their parent) are left
    untouched; only missing ones are added.

    Args:
        session: An open SQLAlchemy session; the caller is responsible for committing.
    """
    categories_data = yaml.safe_load(
        (SEEDS_DIR / "categories.yaml").read_text(encoding="utf-8")
    )

    for position, category_data in enumerate(categories_data):
        main_category = session.scalars(
            select(Category).where(
                Category.parent_id.is_(None), Category.name == category_data["name"]
            )
        ).first()
        if main_category is None:
            main_category = Category(name=category_data["name"], position=position)
            session.add(main_category)

        existing_child_names = {child.name for child in main_category.children}
        for child_position, child_name in enumerate(category_data["children"]):
            if child_name not in existing_child_names:
                main_category.children.append(
                    Category(name=child_name, position=child_position)
                )


def main() -> None:
    """Load all seed data into the database and commit once at the end."""
    with SessionLocal() as session:
        seed_tags(session)
        seed_categories(session)
        session.commit()


if __name__ == "__main__":
    main()
