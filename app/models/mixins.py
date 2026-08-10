from datetime import datetime, timezone

from sqlalchemy.orm import declared_attr, mapped_column, Mapped, validates
from sqlalchemy.dialects import sqlite
from sqlalchemy import BigInteger


TZ_UTC = timezone.utc
BigIntegerID = BigInteger().with_variant(sqlite.INTEGER(), "sqlite")


class IDFieldMixin:
  @declared_attr
  def id(cls) -> Mapped[int]:
    return mapped_column(BigIntegerID, primary_key=True, index=True, autoincrement=True)


class CreatedAtFieldMixin:
  created_at: Mapped[datetime] = mapped_column(
    nullable=False, default=lambda: datetime.now(tz=TZ_UTC)
  )

  @validates("created_at")
  def validate_created_at(self, _, __):
    # Raises ValueError if created_at is being set.
    # the mapped_column default=... option doesn't trigger @validates
    # method
    raise ValueError("created_at cannot be directly assigned or modified once set.")


class UpdatedAtFieldMixin:
  updated_at: Mapped[datetime] = mapped_column(
    nullable=False,
    default=lambda: datetime.now(tz=TZ_UTC),
    onupdate=lambda: datetime.now(tz=TZ_UTC),
  )

  @validates("updated_at")
  def validate_updated_at(self, _, __):
    raise ValueError("updated_at cannot be directly assigned.")
