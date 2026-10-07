"""Association table linking recipes and tags."""

from sqlalchemy import Column, ForeignKey, Table

from app.models.base import Base

recipe_tags = Table(
    "recipe_tags",
    Base.metadata,
    Column("recipe_id", ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "tag_id",
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)
