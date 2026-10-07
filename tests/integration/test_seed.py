"""Tests for the seed data loader."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Category, Tag, TagGroup
from scripts.seed import seed_categories, seed_tags


def test_seed_tags_is_idempotent(db_session: Session) -> None:
    """Running seed_tags twice does not create duplicate tag groups or tags."""
    seed_tags(db_session)
    db_session.commit()

    tag_group_count = len(db_session.scalars(select(TagGroup)).all())
    tag_count = len(db_session.scalars(select(Tag)).all())
    assert tag_group_count > 0
    assert tag_count > 0

    seed_tags(db_session)
    db_session.commit()

    assert len(db_session.scalars(select(TagGroup)).all()) == tag_group_count
    assert len(db_session.scalars(select(Tag)).all()) == tag_count


def test_seed_categories_is_idempotent(db_session: Session) -> None:
    """Running seed_categories twice does not create duplicate categories."""
    seed_categories(db_session)
    db_session.commit()

    category_count = len(db_session.scalars(select(Category)).all())
    assert category_count > 0

    seed_categories(db_session)
    db_session.commit()

    assert len(db_session.scalars(select(Category)).all()) == category_count
