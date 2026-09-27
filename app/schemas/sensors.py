from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.models.sensor import Sensor, UNITS_CHOICES
from app.schemas.devices import DeviceSchema


class SensorSchema(BaseModel):
  model_config = ConfigDict(extra="allow")

  id: int
  device_id: UUID
  presentation_name: str
  key_name: str
  unit: str
  created_at: datetime

  @model_validator(mode="before")
  @classmethod
  def add_related_device(cls, data: any):
    if isinstance(data, Sensor):
      data_dict = {
        "id": data.id,
        "device_id": data.device_id,
        "presentation_name": data.presentation_name,
        "key_name": data.key_name,
        "unit": data.unit,
        "created_at": data.created_at,
      }

      try:
        data.device
      except Exception as _:
        return data_dict
      else:
        data_dict["device"] = DeviceSchema.model_validate(
          data.device, from_attributes=True
        )
        return data_dict


class CreateSensorSchema(BaseModel):
  device_id: UUID
  presentation_name: str
  key_name: str
  unit: str

  @field_validator("unit", mode="before")
  @classmethod
  def validate_unit(cls, unit: str):
    unit = unit.strip()

    if unit == "" or unit not in UNITS_CHOICES:
      raise ValueError(
        f"Given unit {unit} is empty string or not an valid unit option."
      )

    return unit


class UpdateSensorSchema(BaseModel):
  device_id: UUID | None = None
  presentation_name: str | None = None
  key_name: str | None = None
  unit: str | None = None

  @field_validator("unit", mode="before")
  @classmethod
  def validate_unit(cls, unit: str):
    unit = unit.strip()

    if unit == "" or unit not in UNITS_CHOICES:
      raise ValueError(
        f"Given unit {unit} is empty string or not an valid unit option."
      )

    return unit
