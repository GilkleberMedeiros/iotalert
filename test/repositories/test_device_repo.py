from datetime import datetime
import uuid

from sqlalchemy import delete

from app.models.device import (
  Device,
  DeviceRepository,
)
from test.conftest import InMemoryDatabaseTestCase, get_session


class TestDeviceRepository__init_instances(InMemoryDatabaseTestCase):
  async def asyncSetUp(self):
    await super().asyncSetUp()
    async with get_session() as session:
      self.repo = DeviceRepository(session)

      device_data = [
        {"name": "Device 1", "location": "Location 1"},
        {
          "name": "Device 2",
          "location": "Location 2",
          "status": Device.Status.ACTIVE,
        },
      ]

      devices = await self.repo.create(device_data)
      if not isinstance(devices, list):
        devices = [devices]
      await session.commit()  # Ensure the devices are persisted in the session
      self.device_ids = [device.id for device in devices]

  async def asyncTearDown(self):
    async with get_session() as session:
      smt = delete(Device)
      await session.execute(smt)
      await session.commit()

    return await super().asyncTearDown()


class TestDeviceRepository_create(InMemoryDatabaseTestCase):
  async def test_create_single_device(self):
    async with get_session() as session:
      repo = DeviceRepository(session)

      device_data = {
        "name": "Test Device",
        "location": "Test Location",
      }

      device = await repo.create(device_data)
      await session.commit()  # Commit the session to persist the changes

      self.assertIsInstance(device, Device)
      self.assertIsNotNone(device.id)
      self.assertEqual(device.name, device_data["name"])
      self.assertEqual(device.location, device_data["location"])
      # Should set status as ACTIVE by default
      self.assertEqual(device.status, Device.Status.ACTIVE)
      self.assertIsNotNone(device.token_id)
      self.assertIsInstance(device.created_at, datetime)
      self.assertIsInstance(device.updated_at, datetime)

  async def test_create_multiple_devices(self):
    async with get_session() as session:
      repo = DeviceRepository(session)

      devices_data = [
        {
          "name": "Device 1",
          "location": "Location 1",
          "status": "active",
        },
        {
          "name": "Device 2",
          "location": "Location 2",
          "status": "inactive",
        },
      ]

      devices = await repo.create(devices_data)
      await session.commit()  # Commit the session to persist the changes

      self.assertIsInstance(devices, list)
      self.assertEqual(len(devices), 2)
      self.assertIsInstance(devices[0], Device)
      self.assertIsInstance(devices[1], Device)
      self.assertEqual(devices[0].name, devices_data[0]["name"])
      self.assertEqual(devices[1].name, devices_data[1]["name"])

  async def test_create_device_with_invalid_status(self):
    async with get_session() as session:
      repo = DeviceRepository(session)

      device_data = {
        "name": "Invalid Status Device",
        "location": "Test Location",
        "status": "invalid_status",  # Invalid status
      }

      with self.assertRaises(ValueError):
        await repo.create(device_data)

  async def test_create_device_with_empty_strings(self):
    async with get_session() as session:
      repo = DeviceRepository(session)

      device_data = {
        "name": "",  # Empty name
        "location": "Test Location",
      }

      with self.assertRaises(ValueError):
        await repo.create(device_data)

      device_data = {
        "name": "Test Device",
        "location": "",  # Empty location
      }

      with self.assertRaises(ValueError):
        await repo.create(device_data)


class TestDeviceRepository_get(TestDeviceRepository__init_instances):
  async def test_get_existing_device(self):
    async with get_session() as session:
      device_id = self.device_ids[0]
      repo = DeviceRepository(session)

      # Get the first device created in setUp
      device = await repo.get(device_id)

      self.assertIsInstance(device, Device)
      self.assertEqual(device.id, device_id)
      self.assertEqual(device.name, "Device 1")
      self.assertEqual(device.location, "Location 1")

  async def test_get_non_existing_device(self):
    async with get_session() as session:
      repo = DeviceRepository(session)

      device = await repo.get(uuid.uuid4())  # Non-existing ID

      self.assertIsNone(device)

  async def test_get_can_receive_str_as_id(self):
    async with get_session() as session:
      device_id = self.device_ids[0]
      repo = DeviceRepository(session)

      # Get the first device created in setUp
      device = await repo.get(str(device_id))

      self.assertIsInstance(device, Device)
      self.assertEqual(device.id, device_id)


class TestDeviceRepository__list(TestDeviceRepository__init_instances):
  async def test_list_devices(self):
    async with get_session() as session:
      repo = DeviceRepository(session)

      devices = (await repo.list()).all()

      self.assertIsInstance(devices, list)
      self.assertEqual(len(devices), 2)
      self.assertIsInstance(devices[0], Device)
      self.assertIsInstance(devices[1], Device)

  async def test_list_empty(self):
    async with get_session() as session:
      # Clear all devices first
      smt = delete(Device)
      await session.execute(smt)
      await session.commit()

      repo = DeviceRepository(session)

      devices = (await repo.list()).all()

      self.assertIsInstance(devices, list)
      self.assertEqual(len(devices), 0)


class TestDeviceRepository__update(TestDeviceRepository__init_instances):
  async def test_update_existing_device(self):
    async with get_session() as session:
      device_id = self.device_ids[0]
      repo = DeviceRepository(session)

      update_data = {
        "name": "Updated Device Name",
        "location": "Updated Location",
        "status": "inactive",
      }

      updated_device = await repo.update(device_id, update_data)
      await session.commit()

      self.assertIsInstance(updated_device, Device)
      self.assertEqual(updated_device.id, device_id)
      self.assertEqual(updated_device.name, update_data["name"])
      self.assertEqual(updated_device.location, update_data["location"])
      self.assertEqual(updated_device.status, Device.Status(update_data["status"]))

  async def test_update_non_existing_device(self):
    async with get_session() as session:
      repo = DeviceRepository(session)

      update_data = {
        "name": "Non-existing Device",
        "location": "Some Location",
        "status": "active",
      }

      with self.assertRaises(Exception):
        await repo.update(999, update_data)  # Non-existing ID

  async def test_update_cant_update_id(self):
    async with get_session() as session:
      device_id = self.device_ids[0]
      repo = DeviceRepository(session)

      update_data = {
        "id": "new_id",
      }

      updated_device = await repo.update(device_id, update_data)
      await session.commit()

      self.assertEqual(updated_device.id, device_id)  # ID should not change

  async def test_update_can_receive_id_as_str(self):
    async with get_session() as session:
      device_id = self.device_ids[0]
      repo = DeviceRepository(session)

      update_data = {
        "name": "Updated Device Name",
      }

      updated_device = await repo.update(str(device_id), update_data)
      await session.commit()

      self.assertIsInstance(updated_device, Device)
      self.assertEqual(updated_device.id, device_id)
      self.assertEqual(updated_device.name, update_data["name"])

  async def test_update_with_invalid_status(self):
    async with get_session() as session:
      device_id = self.device_ids[0]
      repo = DeviceRepository(session)

      update_data = {
        "status": "invalid_status",  # Invalid status
      }

      with self.assertRaises(ValueError):
        await repo.update(device_id, update_data)

  async def test_update_fields_to_empty_strings(self):
    async with get_session() as session:
      device_id = self.device_ids[1]
      repo = DeviceRepository(session)

      update_data = {"name": ""}

      with self.assertRaises(ValueError):
        await repo.update(device_id, update_data)

      update_data2 = {"location": ""}

      with self.assertRaises(ValueError):
        await repo.update(device_id, update_data2)

  async def test_update_cant_update_created_at(self):
    async with get_session() as session:
      device_id = self.device_ids[0]
      repo = DeviceRepository(session)

      update_data = {"created_at": datetime.now()}

      with self.assertRaises(ValueError):
        await repo.update(device_id, update_data)

  async def test_update_changes_updated_at(self):
    async with get_session() as session:
      device_id = self.device_ids[0]
      repo = DeviceRepository(session)

      original_device = await repo.get(device_id)
      original_updated_at = original_device.updated_at

      update_data = {"name": "Updated Name"}
      updated_device = await repo.update(device_id, update_data)
      await session.commit()

      self.assertNotEqual(updated_device.updated_at, original_updated_at)


class TestDeviceRepository__delete(TestDeviceRepository__init_instances):
  async def test_delete_existing_device(self):
    async with get_session() as session:
      device_id = self.device_ids[0]
      repo = DeviceRepository(session)

      await repo.delete(device_id)
      await session.commit()

      deleted_device = await repo.get(device_id)
      self.assertIsNone(deleted_device)

  async def test_delete_non_existing_device(self):
    async with get_session() as session:
      repo = DeviceRepository(session)

      with self.assertRaises(Exception):
        await repo.delete(999)  # Non-existing ID

  async def test_delete_can_receive_id_as_str(self):
    async with get_session() as session:
      device_id = self.device_ids[0]
      repo = DeviceRepository(session)

      await repo.delete(str(device_id))
      await session.commit()

      deleted_device = await repo.get(device_id)
      remaining_devices = await repo.list()
      self.assertIsNone(deleted_device)
      self.assertEqual(len(remaining_devices.all()), 1)
