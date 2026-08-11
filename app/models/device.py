from typing import TYPE_CHECKING, Literal, TypedDict, Union, Set
from uuid import uuid4
import secrets

from sqlalchemy import String, UUID
from sqlalchemy.orm import Mapped, mapped_column, validates, declared_attr, relationship

from app.models.base import BaseModel, ModelRepository
from app.models.mixins import CreatedAtFieldMixin, UpdatedAtFieldMixin

if TYPE_CHECKING:
  from app.models.sensor import Sensor


class Device(BaseModel, CreatedAtFieldMixin, UpdatedAtFieldMixin):
  __tablename__ = "devices"

  class DeviceStatus:
    ACTIVE = "active"
    INACTIVE = "inactive"
    ANOMALY = "anomaly"
    ACTIVE_T = Literal["active"]
    INACTIVE_T = Literal["inactive"]
    ANOMALY_T = Literal["anomaly"]

  name: Mapped[str] = mapped_column(String(255))
  location: Mapped[str] = mapped_column(String(255))

  status: Mapped[
    Union[DeviceStatus.ACTIVE_T, DeviceStatus.INACTIVE_T, DeviceStatus.ANOMALY_T]
  ] = mapped_column(String(40), default=DeviceStatus.ACTIVE, nullable=False)
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
    valid_statuses = {
      self.DeviceStatus.ACTIVE,
      self.DeviceStatus.INACTIVE,
      self.DeviceStatus.ANOMALY,
    }

    if value not in valid_statuses:
      raise ValueError(f"{key} must be one of DeviceStatus values.")
    return value


class CreateDeviceData(TypedDict):
  name: str
  location: str
  status: Union[
    Device.DeviceStatus.ACTIVE_T,
    Device.DeviceStatus.INACTIVE_T,
    Device.DeviceStatus.ANOMALY_T,
  ]


class UpdateDeviceData(TypedDict, total=False):
  name: str
  location: str
  status: Union[
    Device.DeviceStatus.ACTIVE_T,
    Device.DeviceStatus.INACTIVE_T,
    Device.DeviceStatus.ANOMALY_T,
  ]


class DeviceRepository(ModelRepository[Device, CreateDeviceData, UpdateDeviceData]):
  model = Device
  pass
