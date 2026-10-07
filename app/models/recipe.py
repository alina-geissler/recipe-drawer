"""SQLAlchemy model for a recipe."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import RecipeStatus, SourceType
from app.models.base import Base, enum_column
from app.models.recipe_tag import recipe_tags

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.image import Image
    from app.models.ingredient import Ingredient
    from app.models.step import Step
    from app.models.tag import Tag


class Recipe(Base):
    """A recipe with its metadata, source, review status and relationships."""

    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    servings: Mapped[str | None]
    active_time_minutes: Mapped[int | None]
    total_time_minutes: Mapped[int | None]
    source_notes: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[int | None] = mapped_column(  # how to: "required when saved"?
        ForeignKey("categories.id"), index=True
    )
    category: Mapped[Category | None] = relationship()
    source_type: Mapped[SourceType] = mapped_column(enum_column(SourceType))
    source_url: Mapped[str | None] = mapped_column(index=True)
    status: Mapped[RecipeStatus] = mapped_column(enum_column(RecipeStatus), index=True)
    suggested_tags: Mapped[list[dict[str, str]] | None] = mapped_column(JSON)
    extraction_method: Mapped[str | None]
    extraction_model: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    ingredients: Mapped[list[Ingredient]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="Ingredient.position",
    )

    steps: Mapped[list[Step]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan", order_by="Step.position"
    )

    tags: Mapped[list[Tag]] = relationship(
        secondary=recipe_tags, back_populates="recipes"
    )

    images: Mapped[list[Image]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan", order_by="Image.position"
    )
