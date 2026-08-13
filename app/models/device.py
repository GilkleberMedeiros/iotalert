import enum
from typing import TYPE_CHECKING, Literal, TypedDict, Set
from uuid import uuid4
import secrets

from sqlalchemy import String, UUID, Enum
from sqlalchemy.orm import Mapped, mapped_column, validates, declared_attr, relationship

from app.models.base import BaseModel, ModelRepository
from app.models.mixins import CreatedAtFieldMixin, UpdatedAtFieldMixin

if TYPE_CHECKING:
  from app.models.sensor import Sensor


class Device(BaseModel, CreatedAtFieldMixin, UpdatedAtFieldMixin):
  __tablename__ = "devices"

  class Status(enum.Enum):
    ACTIVE: Literal["active"] = "active"
    INACTIVE: Literal["inactive"] = "inactive"
    ANOMALY: Literal["anomaly"] = "anomaly"

  name: Mapped[str] = mapped_column(String(255))
  location: Mapped[str] = mapped_column(String(255))

  status: Mapped[enum.Enum] = mapped_column(
    Enum(Status), default=Status.ACTIVE, nullable=False
  )
  token_id: Mapped[str] = mapped_column(
    default=lambda: "device_token_" + secrets.token_urlsafe(64), unique=True, index=True
  )

  @declared_attr
  def id(cls):
    return mapped_column(
      UUID(as_uuid=True), primary_key=True, index=True, default=uuid4
    )

  sensors: Mapped[Set["Sensor"]] = relationship(
    back_populates="device", cascade="all, delete"
  )

  @validates("name", "location")
  def validate_non_empty_string(self, key, value):
    if not isinstance(value, str) or not value.strip():
      raise ValueError(f"{key} must be a non-empty string.")
    return value

  @validates("status")
  def validate_status(self, key, value):
    # Accept a Device.Status enum member or a string (case-insensitive)
    if isinstance(value, self.Status):
      return value

    if isinstance(value, str):
      valid_values = {s.value for s in self.Status}
      valid_names = {s.name for s in self.Status}
      valid_statuses = {*valid_names, *valid_values}

      if value not in valid_statuses:
        raise ValueError(f"{key} must be one of: {valid_values}")

      return self.Status[value.upper()]

    raise ValueError(
      f"{key} must be a Device.Status or string. Got {type(value)} instead."
    )


class CreateDeviceData(TypedDict):
  name: str
  location: str
  status: str | Device.Status


class UpdateDeviceData(TypedDict, total=False):
  name: str
  location: str
  status: str | Device.Status


class DeviceRepository(ModelRepository[Device, CreateDeviceData, UpdateDeviceData]):
  model = Device
  pass
