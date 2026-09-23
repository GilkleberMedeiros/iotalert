import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.device import Device


class DeviceSchema(BaseModel):
  id: UUID
  name: str
  location: str
  status: Device.Status
  created_at: datetime
  updated_at: datetime


class CreateDeviceResSchema(DeviceSchema):
  token_id: str


EXCLUDED_STATUS = {"anomaly"}
DeviceStatus = enum.Enum(
  "DeviceStatus",
  {
    member.value: member.value
    for _, member in Device.Status.__members__.items()
    if member.value not in EXCLUDED_STATUS
  },
)


class CreateDeviceSchema(BaseModel):
  model_config = ConfigDict(use_enum_values=True)

  name: str
  location: str
  status: DeviceStatus = Device.Status.ACTIVE


class UpdateDeviceSchema(BaseModel):
  model_config = ConfigDict(use_enum_values=True)

  name: str | None = None
  location: str | None = None
