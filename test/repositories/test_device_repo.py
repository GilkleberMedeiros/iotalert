from datetime import datetime
from unittest import TestCase

from app.db import get_session
from app.models.device import (
  Device,
  DeviceRepository,
)


class TestDeviceRepository__init_instances(TestCase):
  def setUp(self):
    with next(get_session()) as session:
      self.repo = DeviceRepository(session)

      device_data = [
        {"name": "Device 1", "location": "Location 1"},
        {"name": "Device 2", "location": "Location 2", "status": "inactive"},
      ]

      devices = self.repo.create(device_data)
      session.commit()  # Ensure the devices are persisted in the session
      self.device_ids = [device.id for device in devices]

    return super().setUp()

  def tearDown(self):
    with next(get_session()) as session:
      session.query(Device).delete()
      session.commit()

    return super().tearDown()


class TestDeviceRepository_create(TestCase):
  def test_create_single_device(self):
    with next(get_session()) as session:
      repo = DeviceRepository(session)

      device_data = {
        "name": "Test Device",
        "location": "Test Location",
      }

      device = repo.create(device_data)
      session.commit()  # Commit the session to persist the changes

      self.assertIsInstance(device, Device)
      self.assertIsNotNone(device.id)
      self.assertEqual(device.name, device_data["name"])
      self.assertEqual(device.location, device_data["location"])
      # Should set status as ACTIVE by default
      self.assertEqual(device.status, Device.DeviceStatus.ACTIVE)
      self.assertIsNotNone(device.token_id)
      self.assertIsInstance(device.created_at, datetime)
      self.assertIsInstance(device.updated_at, datetime)

  def test_create_multiple_devices(self):
    with next(get_session()) as session:
      repo = DeviceRepository(session)

      devices_data = [
        {"name": "Device 1", "location": "Location 1", "status": "active"},
        {"name": "Device 2", "location": "Location 2", "status": "inactive"},
      ]

      devices = repo.create(devices_data)
      session.commit()  # Commit the session to persist the changes

      self.assertIsInstance(devices, list)
      self.assertEqual(len(devices), 2)
      self.assertIsInstance(devices[0], Device)
      self.assertIsInstance(devices[1], Device)
      self.assertEqual(devices[0].name, devices_data[0]["name"])
      self.assertEqual(devices[1].name, devices_data[1]["name"])

  def test_create_device_with_invalid_status(self):
    with next(get_session()) as session:
      repo = DeviceRepository(session)

      device_data = {
        "name": "Invalid Status Device",
        "location": "Test Location",
        "status": "invalid_status",  # Invalid status
      }

      with self.assertRaises(ValueError):
        repo.create(device_data)

  def test_create_device_with_empty_strings(self):
    with next(get_session()) as session:
      repo = DeviceRepository(session)

      device_data = {
        "name": "",  # Empty name
        "location": "Test Location",
      }

      with self.assertRaises(ValueError):
        repo.create(device_data)

      device_data = {
        "name": "Test Device",
        "location": "",  # Empty location
      }

      with self.assertRaises(ValueError):
        repo.create(device_data)


class TestDeviceRepository_get(TestDeviceRepository__init_instances):
  def test_get_existing_device(self):
    with next(get_session()) as session:
      device_id = self.device_ids[0]
      repo = DeviceRepository(session)

      # Get the first device created in setUp
      device = repo.get(device_id)

      self.assertIsInstance(device, Device)
      self.assertEqual(device.id, device_id)
      self.assertEqual(device.name, "Device 1")
      self.assertEqual(device.location, "Location 1")

  def test_get_non_existing_device(self):
    with next(get_session()) as session:
      repo = DeviceRepository(session)

      device = repo.get(999)  # Non-existing ID

      self.assertIsNone(device)


class TestDeviceRepository__list(TestDeviceRepository__init_instances):
  def test_list_devices(self):
    with next(get_session()) as session:
      repo = DeviceRepository(session)

      devices = repo.list().all()

      self.assertIsInstance(devices, list)
      self.assertEqual(len(devices), 2)
      self.assertIsInstance(devices[0], Device)
      self.assertIsInstance(devices[1], Device)

  def test_list_empty(self):
    with next(get_session()) as session:
      # Clear all devices first
      session.query(Device).delete()
      session.commit()

      repo = DeviceRepository(session)

      devices = repo.list().all()

      self.assertIsInstance(devices, list)
      self.assertEqual(len(devices), 0)


class TestDeviceRepository__update(TestDeviceRepository__init_instances):
  def test_update_existing_device(self):
    with next(get_session()) as session:
      device_id = self.device_ids[0]
      repo = DeviceRepository(session)

      update_data = {
        "name": "Updated Device Name",
        "location": "Updated Location",
        "status": "inactive",
      }

      updated_device = repo.update(device_id, update_data)
      session.commit()

      self.assertIsInstance(updated_device, Device)
      self.assertEqual(updated_device.id, device_id)
      self.assertEqual(updated_device.name, update_data["name"])
      self.assertEqual(updated_device.location, update_data["location"])
      self.assertEqual(updated_device.status, update_data["status"])

  def test_update_non_existing_device(self):
    with next(get_session()) as session:
      repo = DeviceRepository(session)

      update_data = {
        "name": "Non-existing Device",
        "location": "Some Location",
        "status": "active",
      }

      with self.assertRaises(Exception):
        repo.update(999, update_data)  # Non-existing ID

  def test_update_cant_update_id(self):
    with next(get_session()) as session:
      device_id = self.device_ids[0]
      repo = DeviceRepository(session)

      update_data = {
        "id": "new_id",
      }

      updated_device = repo.update(device_id, update_data)
      session.commit()

      self.assertEqual(updated_device.id, device_id)  # ID should not change

  def test_update_with_invalid_status(self):
    with next(get_session()) as session:
      device_id = self.device_ids[0]
      repo = DeviceRepository(session)

      update_data = {
        "status": "invalid_status",  # Invalid status
      }

      with self.assertRaises(ValueError):
        repo.update(device_id, update_data)

  def test_update_fields_to_empty_strings(self):
    with next(get_session()) as session:
      device_id = self.device_ids[1]
      repo = DeviceRepository(session)

      update_data = {"name": ""}

      with self.assertRaises(ValueError):
        repo.update(device_id, update_data)

      update_data2 = {"location": ""}

      with self.assertRaises(ValueError):
        repo.update(device_id, update_data2)

  def test_update_cant_update_created_at(self):
    with next(get_session()) as session:
      device_id = self.device_ids[0]
      repo = DeviceRepository(session)

      update_data = {"created_at": datetime.now()}

      with self.assertRaises(ValueError):
        repo.update(device_id, update_data)

  def test_update_changes_updated_at(self):
    with next(get_session()) as session:
      device_id = self.device_ids[0]
      repo = DeviceRepository(session)

      original_device = repo.get(device_id)
      original_updated_at = original_device.updated_at

      update_data = {"name": "Updated Name"}
      updated_device = repo.update(device_id, update_data)
      session.commit()

      self.assertNotEqual(updated_device.updated_at, original_updated_at)


class TestDeviceRepository__delete(TestDeviceRepository__init_instances):
  def test_delete_existing_device(self):
    with next(get_session()) as session:
      device_id = self.device_ids[0]
      repo = DeviceRepository(session)

      repo.delete(device_id)
      session.commit()

      deleted_device = repo.get(device_id)
      self.assertIsNone(deleted_device)

  def test_delete_non_existing_device(self):
    with next(get_session()) as session:
      repo = DeviceRepository(session)

      with self.assertRaises(Exception):
        repo.delete(999)  # Non-existing ID
