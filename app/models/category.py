"""SQLAlchemy model for a recipe category."""

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Category(Base):
    """A main category or subcategory, self-referencing via parent_id."""

    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("parent_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]  # how to make it unique within the same parent?
    position: Mapped[int]
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id"), index=True
    )

    parent: Mapped[Category | None] = relationship(
        back_populates="children", remote_side="Category.id"
    )

    children: Mapped[list[Category]] = relationship(
        back_populates="parent", order_by="Category.position"
    )
