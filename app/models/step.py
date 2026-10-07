"""SQLAlchemy model for a recipe instruction step."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.recipe import Recipe


class Step(Base):
    """One instruction step within a specific recipe."""

    __tablename__ = "steps"
    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True
    )
    recipe: Mapped[Recipe] = relationship(back_populates="steps")
    position: Mapped[int]
    group_label: Mapped[str | None]
    text: Mapped[str] = mapped_column(Text)
