"""SQLAlchemy model for a tag group."""

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.tag import Tag


class TagGroup(Base):
    """A group that one or more tags belong to, e.g. "Diet"."""

    __tablename__ = "tag_groups"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    position: Mapped[int]

    tags: Mapped[list[Tag]] = relationship(
        back_populates="tag_group", order_by="Tag.name"
    )
