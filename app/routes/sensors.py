from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.exc import NoResultFound

from app.db import SessionDep
from app.errors import APIError
from app.models.device import DeviceRepository
from app.models.sensor import Sensor, SensorRepository
from app.schemas.params import PaginationParams
from app.schemas.sensors import CreateSensorSchema, UpdateSensorSchema, SensorSchema

router = APIRouter(prefix="/sensors", tags=["Sensors"])


@router.post(
  path="",
  status_code=201,
  response_model=SensorSchema,
)
async def create_sensor(
  sensor: CreateSensorSchema, session: SessionDep
) -> SensorSchema:
  try:
    repod = DeviceRepository(session)
    if await repod.get(sensor.device_id) is None:
      raise NoResultFound()

    repo = SensorRepository(session)
    created = await repo.create(sensor.model_dump())
    await session.commit()

    return created
  except ValueError as e:
    raise APIError(status_code=400, detail=str(e))
  except NoResultFound:
    raise APIError(
      status_code=404,
      detail=f"Couldn't find device with given id {sensor.device_id} to bind to sensor.",
    )


@router.get("/{sensor_id}", response_model=SensorSchema)
async def get_sensor(
  sensor_id: str,
  session: SessionDep,
  include_device: bool = True,
) -> SensorSchema:
  try:
    repo = SensorRepository(session)
    sensor = await repo.get(sensor_id, [Sensor.device] if include_device else ...)

    if sensor is None:
      raise APIError(status_code=404, detail="Sensor was't found by given id.")

    return sensor
  except APIError:
    raise
  except ValueError as e:
    raise APIError(status_code=400, detail=str(e))


@router.get("")
async def list_sensors(
  session: SessionDep,
  pagination: Annotated[PaginationParams, Depends()],
  include_devices: bool = False,
) -> list[SensorSchema]:
  try:
    repo = SensorRepository(session)
    page_data = pagination.model_dump()
    related = [Sensor.device] if include_devices else ...

    return (await repo.list(page_data, related)).all()
  except:
    raise


@router.patch("/{sensor_id}")
async def update_sensor(
  sensor_id: str, sensor: UpdateSensorSchema, session: SessionDep
) -> SensorSchema:
  try:
    if sensor.device_id is not None:
      repod = DeviceRepository(session)
      if await repod.get(sensor.device_id) is None:
        raise APIError(
          status_code=404,
          detail="Couldn't find device with given id to bind to sensor.",
        )

    repo = SensorRepository(session)
    updated = await repo.update(sensor_id, sensor.model_dump(exclude_unset=True))
    await session.commit()

    return updated
  except ValueError as e:
    raise APIError(status_code=400, detail=str(e))
  except NoResultFound:
    raise APIError(status_code=404, detail="Couldn't find sensor with the given id.")


@router.delete("/{sensor_id}")
async def delete_sensor(sensor_id: str, session: SessionDep):
  try:
    repo = SensorRepository(session)

    await repo.delete(sensor_id)
    await session.commit()

    return {"detail": "Sensor with given id was deleted.", "success": True}
  except NoResultFound:
    raise APIError(status_code=404, detail="Couldn't find sensor with the given id.")
