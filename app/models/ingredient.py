"""SQLAlchemy model for a recipe ingredient."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.recipe import Recipe


class Ingredient(Base):
    """One ingredient line within a specific recipe."""

    __tablename__ = "ingredients"
    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True
    )
    recipe: Mapped[Recipe] = relationship(back_populates="ingredients")
    position: Mapped[int]
    group_label: Mapped[str | None]
    quantity: Mapped[float | None]
    quantity_max: Mapped[float | None]
    unit: Mapped[str | None]
    name: Mapped[str]
    base_name: Mapped[str] = mapped_column(index=True)
    note: Mapped[str | None]
