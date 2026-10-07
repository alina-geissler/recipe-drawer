"""SQLAlchemy model for a tag."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.recipe_tag import recipe_tags

if TYPE_CHECKING:
    from app.models.recipe import Recipe
    from app.models.tag_group import TagGroup


class Tag(Base):
    """A tag describing an additional recipe property, e.g. "vegan"."""

    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    tag_group_id: Mapped[int] = mapped_column(ForeignKey("tag_groups.id"), index=True)
    tag_group: Mapped[TagGroup] = relationship(back_populates="tags")
    is_pinned: Mapped[bool] = mapped_column(default=False, server_default=false())

    recipes: Mapped[list[Recipe]] = relationship(
        secondary=recipe_tags, back_populates="tags"
    )
