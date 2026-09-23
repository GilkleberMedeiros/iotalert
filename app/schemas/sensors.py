from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.models.sensor import UNITS_CHOICES


class SensorSchema(BaseModel):
  id: int
  device_id: UUID
  presentation_name: str
  key_name: str
  unit: str
  created_at: datetime


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
