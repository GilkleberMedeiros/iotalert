from fastapi import APIRouter
from sqlalchemy.exc import NoResultFound

from app.db import SessionDep
from app.errors import APIError
from app.models.device import Device, DeviceRepository
from app.schemas.devices import CreateDeviceSchema, DeviceSchema, UpdateDeviceSchema


router = APIRouter(prefix="/devices", tags=["Devices"])


@router.post(
  path="",
  status_code=201,
  response_model=DeviceSchema,
)
async def create_device(
  device: CreateDeviceSchema, session: SessionDep
) -> DeviceSchema:
  try:
    repo = DeviceRepository(session)
    created: Device = await repo.create(device.model_dump())
    await session.commit()

    return created
  except ValueError as e:
    raise APIError(status_code=400, detail=str(e))


@router.get("/{device_id}", response_model=DeviceSchema)
async def get_device(device_id: str, session: SessionDep) -> DeviceSchema:
  try:
    repo = DeviceRepository(session)
    device = await repo.get(device_id)

    if device is None:
      raise APIError(status_code=404, detail="Device was't found by given id.")

    return device
  except APIError:
    raise
  except ValueError as e:
    raise APIError(status_code=400, detail=str(e))


@router.get("")
async def list_devices(session: SessionDep) -> list[DeviceSchema]:
  try:
    repo = DeviceRepository(session)

    return (await repo.list()).all()
  except:
    raise


@router.patch("/{device_id}")
async def update_device(
  device_id: str, device: UpdateDeviceSchema, session: SessionDep
) -> DeviceSchema:
  try:
    repo = DeviceRepository(session)
    updated = await repo.update(device_id, device.model_dump(exclude_unset=True))
    await session.commit()

    return updated
  except ValueError as e:
    raise APIError(status_code=400, detail=str(e))
  except NoResultFound:
    raise APIError(status_code=404, detail="Couldn't find device with the given id.")


@router.delete("/{device_id}")
async def delete_device(device_id: str, session: SessionDep):
  try:
    repo = DeviceRepository(session)

    await repo.delete(device_id)
    await session.commit()

    return {"detail": "Device with given id was deleted.", "success": True}
  except NoResultFound:
    raise APIError(status_code=404, detail="Couldn't find device with the given id.")


@router.patch("/activate/{device_id}")
async def activate_device(device_id: str, session: SessionDep):
  try:
    repo = DeviceRepository(session)

    await repo.update(device_id, {"status": Device.Status.ACTIVE})
    await session.commit()

    return {"detail": "Device with given id was activated.", "success": True}
  except NoResultFound:
    raise APIError(404, detail="Couldn't find device with the given id.")


@router.patch("/inactivate/{device_id}")
async def inactivate_device(device_id: str, session: SessionDep):
  try:
    repo = DeviceRepository(session)

    await repo.update(device_id, {"status": Device.Status.INACTIVE})
    await session.commit()

    return {"detail": "Device with given id was inactivated.", "success": True}
  except NoResultFound:
    raise APIError(404, detail="Couldn't find device with the given id.")
