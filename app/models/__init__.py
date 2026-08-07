from .base import Base, BaseModel
from .device import Device


# Import all models to ensure they are registered with SQLAlchemy
__MODELS__ = [Base, BaseModel, Device]
__ALL__ = [
  "Base",
  "IDFieldMixin",
  "BaseModel",
  "ModelRepository",
  "Device",
  "DeviceRepository",
]
