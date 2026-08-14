from datetime import datetime

from sqlalchemy import select, delete

from app.models.device import Device
from app.models.sensor import (
  Sensor,
  SensorRepository,
)
from test.conftest import InMemoryDatabaseTestCase, get_session


class TestSensorRepository__init_instances(InMemoryDatabaseTestCase):
  async def asyncSetUp(self):
    setup = await super().asyncSetUp()
    async with get_session() as session:
      self.repo = SensorRepository(session)
      d_status = Device.Status
      device_data = [
        {"name": "Device 1", "location": "SensorRepo Tests"},
        {
          "name": "Device 2",
          "location": "SensorRepo Tests",
          "status": d_status.INACTIVE,
        },
      ]
      devices = [Device(**d) for d in device_data]

      session.add_all(devices)
      await session.flush()
      self.device_ids = [d.id for d in devices]

      sensor_data = [
        {
          "device_id": self.device_ids[0],
          "presentation_name": "Sensor 1",
          "key_name": "sensor_1",
          "unit": "celsius",
        },
        {
          "device_id": self.device_ids[0],
          "presentation_name": "Sensor 2",
          "key_name": "sensor_2",
          "unit": "degree",
        },
      ]

      sensors = await self.repo.create(sensor_data)
      await session.commit()  # Ensure the sensors are persisted in the session
      self.sensor_ids = [sensor.id for sensor in sensors]

    return setup

  async def asyncTearDown(self):
    async with get_session() as session:
      smt = delete(Sensor)
      await session.execute(smt)
      smt2 = delete(Device)
      await session.execute(smt2)
      await session.commit()

    return await super().asyncTearDown()


class TestSensorRepository_create(InMemoryDatabaseTestCase):
  async def asyncSetUp(self):
    setup = await super().asyncSetUp()
    async with get_session() as session:
      self.repo = SensorRepository(session)
      d_status = Device.Status
      device_data = [
        {"name": "Device 1", "location": "SensorRepo Tests"},
        {
          "name": "Device 2",
          "location": "SensorRepo Tests",
          "status": d_status.INACTIVE,
        },
      ]
      devices = [Device(**d) for d in device_data]

      session.add_all(devices)
      await session.commit()
      self.device_ids = [d.id for d in devices]

    return setup

  async def asyncTearDown(self):
    async with get_session() as session:
      smt = delete(Sensor)
      await session.execute(smt)
      await session.commit()

    return await super().asyncTearDown()

  async def test_create_single_sensor(self):
    async with get_session() as session:
      repo = SensorRepository(session)

      sensor_data = {
        "device_id": self.device_ids[0],
        "presentation_name": "Test Sensor",
        "key_name": "test_name",
        "unit": "celsius",
      }

      sensor = await repo.create(sensor_data)
      await session.flush()  # Flush to get the auto-generated id

      self.assertIsInstance(sensor, Sensor)
      self.assertIsNotNone(sensor.id)
      self.assertIsNotNone(sensor.device_id)
      self.assertIsNotNone(await sensor.awaitable_attrs.device)  # Test back_populates
      self.assertEqual(sensor.presentation_name, sensor_data["presentation_name"])
      self.assertEqual(sensor.key_name, sensor_data["key_name"])
      # Should set status as ACTIVE by async default
      self.assertEqual(
        sensor.unit, "celsius"
      )  # unit is stored as string in the database
      self.assertIsInstance(sensor.created_at, datetime)

      await session.commit()  # Commit the session to persist the changes

  async def test_create_multiple_sensors(self):
    async with get_session() as session:
      repo = SensorRepository(session)

      sensors_data = [
        {
          "device_id": self.device_ids[0],
          "presentation_name": "Test Sensor 1",
          "key_name": "test_name_1",
          "unit": "celsius",
        },
        {
          "device_id": self.device_ids[1],
          "presentation_name": "Test Sensor 2",
          "key_name": "test_name_2",
          "unit": "kelvin",
        },
      ]

      sensors = await repo.create(sensors_data)
      await session.commit()  # Commit the session to persist the changes

      self.assertIsInstance(sensors, list)
      self.assertEqual(len(sensors), 2)
      self.assertIsInstance(sensors[0], Sensor)
      self.assertIsInstance(sensors[1], Sensor)
      self.assertEqual(sensors[0].device_id, self.device_ids[0])
      self.assertEqual(sensors[1].device_id, self.device_ids[1])
      self.assertEqual(
        sensors[0].presentation_name, sensors_data[0]["presentation_name"]
      )
      self.assertEqual(
        sensors[1].presentation_name, sensors_data[1]["presentation_name"]
      )

  async def test_create_sensor_with_empty_strings_raises_value_error(self):
    async with get_session() as session:
      repo = SensorRepository(session)

      sensor_data1 = {
        "device_id": self.device_ids[0],
        "presentation_name": "",  # Empty presentation_name
        "key_name": "test_key_name",
        "unit": "kelvin",
      }

      with self.assertRaises(ValueError):
        await repo.create(sensor_data1)

      sensor_data2 = {
        "device_id": self.device_ids[0],
        "presentation_name": "Test Presentation Name",
        "key_name": "",  # Empty key_name
        "unit": "percentage",
      }

      with self.assertRaises(ValueError):
        await repo.create(sensor_data2)

      sensor_data3 = {
        "device_id": self.device_ids[0],
        "presentation_name": "Test Presentation Name",
        "key_name": "test_key_name",
        "unit": "",  # Empty unit
      }

      with self.assertRaises(ValueError):
        await repo.create(sensor_data3)

  async def test_create_sensor_with_invalid_key_name(self):
    async with get_session() as session:
      repo = SensorRepository(session)

      sensor_data = {
        "device_id": self.device_ids[0],
        "presentation_name": "Test Name",
        "key_name": "^key name$",
        "unit": "degree",
      }

      with self.assertRaises(ValueError):
        await repo.create(sensor_data)

  async def test_create_sensor_with_invalid_unit(self):
    async with get_session() as session:
      repo = SensorRepository(session)

      sensor_data = {
        "device_id": self.device_ids[0],
        "presentation_name": "Test Name",
        "key_name": "test_key_name",
        "unit": "<unknow_unit>",
      }

      with self.assertRaises(ValueError):
        await repo.create(sensor_data)


class TestSensorRepository_get(TestSensorRepository__init_instances):
  async def test_get_existing_sensor(self):
    async with get_session() as session:
      sensor_id = self.sensor_ids[0]
      repo = SensorRepository(session)

      # Get the first sensor created in asyncSetUp
      sensor = await repo.get(sensor_id)

      self.assertIsInstance(sensor, Sensor)
      self.assertEqual(sensor.id, sensor_id)
      self.assertEqual(sensor.device_id, self.device_ids[0])
      self.assertEqual(sensor.presentation_name, "Sensor 1")
      self.assertEqual(sensor.key_name, "sensor_1")
      self.assertEqual(sensor.unit.name, "celsius")

  async def test_get_non_existing_sensor(self):
    async with get_session() as session:
      repo = SensorRepository(session)

      sensor = await repo.get(999)  # Non-existing ID

      self.assertIsNone(sensor)


class TestSensorRepository__list(TestSensorRepository__init_instances):
  async def test_list_sensors(self):
    async with get_session() as session:
      repo = SensorRepository(session)

      sensors = (await repo.list()).all()

      self.assertIsInstance(sensors, list)
      self.assertEqual(len(sensors), 2)
      self.assertIsInstance(sensors[0], Sensor)
      self.assertIsInstance(sensors[1], Sensor)

  async def test_list_empty(self):
    async with get_session() as session:
      # Clear all sensors first
      smt = delete(Sensor)
      await session.execute(smt)
      await session.commit()

      repo = SensorRepository(session)

      sensors = (await repo.list()).all()

      self.assertIsInstance(sensors, list)
      self.assertEqual(len(sensors), 0)


class TestSensorRepository__update(TestSensorRepository__init_instances):
  async def test_update_existing_sensor(self):
    async with get_session() as session:
      sensor_id = self.sensor_ids[0]
      repo = SensorRepository(session)

      update_data = {
        "presentation_name": "Updated Sensor Name",
        "key_name": "updated_keyname",
        "unit": "kilowatt",
      }

      updated_sensor = await repo.update(sensor_id, update_data)
      await session.commit()

      self.assertIsInstance(updated_sensor, Sensor)
      self.assertEqual(updated_sensor.id, sensor_id)
      self.assertEqual(
        updated_sensor.presentation_name, update_data["presentation_name"]
      )
      self.assertEqual(updated_sensor.key_name, update_data["key_name"])
      self.assertEqual(updated_sensor.unit, update_data["unit"])

  async def test_update_non_existing_sensor(self):
    async with get_session() as session:
      repo = SensorRepository(session)

      update_data = {
        "presentation_name": "Non-existing Sensor",
        "key_name": "some_key",
        "unit": "kilowatt-hour",
      }

      with self.assertRaises(Exception):
        await repo.update(999, update_data)  # Non-existing ID

  async def test_update_cant_update_id(self):
    async with get_session() as session:
      sensor_id = self.sensor_ids[0]
      repo = SensorRepository(session)

      update_data = {
        "id": "new_id",
      }

      updated_sensor = await repo.update(sensor_id, update_data)
      await session.commit()

      self.assertEqual(updated_sensor.id, sensor_id)  # ID should not change

  async def test_update_can_update_device_id(self):
    async with get_session() as session:
      sensor_id = self.sensor_ids[0]
      repo = SensorRepository(session)
      prev_device_id = (await repo.get(sensor_id)).device_id

      update_data = {
        "device_id": self.device_ids[1],
      }

      updated_sensor = await repo.update(sensor_id, update_data)
      await session.commit()

      self.assertIsInstance(updated_sensor, Sensor)
      self.assertEqual(updated_sensor.id, sensor_id)
      self.assertNotEqual(updated_sensor.device_id, prev_device_id)
      self.assertEqual(updated_sensor.device_id, self.device_ids[1])

  async def test_update_with_invalid_unit_raises_value_error(self):
    async with get_session() as session:
      sensor_id = self.sensor_ids[0]
      repo = SensorRepository(session)

      update_data = {
        "unit": "invalid-unit",  # Invalid unit
      }

      with self.assertRaises(ValueError):
        await repo.update(sensor_id, update_data)

  async def test_update_with_invalid_key_name_raises_value_error(self):
    async with get_session() as session:
      sensor_id = self.sensor_ids[0]
      repo = SensorRepository(session)

      update_data = {"key_name": "Invalid KeyName"}

      with self.assertRaises(ValueError):
        await repo.update(sensor_id, update_data)

  async def test_update_fields_to_empty_strings(self):
    async with get_session() as session:
      sensor_id = self.sensor_ids[1]
      repo = SensorRepository(session)

      update_data = {"presentation_name": ""}

      with self.assertRaises(ValueError):
        await repo.update(sensor_id, update_data)

      update_data2 = {"key_name": ""}

      with self.assertRaises(ValueError):
        await repo.update(sensor_id, update_data2)

      update_data3 = {"unit": ""}

      with self.assertRaises(ValueError):
        await repo.update(sensor_id, update_data3)

  async def test_update_cant_update_created_at(self):
    async with get_session() as session:
      sensor_id = self.sensor_ids[0]
      repo = SensorRepository(session)

      update_data = {"created_at": datetime.now()}

      with self.assertRaises(ValueError):
        await repo.update(sensor_id, update_data)


class TestSensorRepository__delete(TestSensorRepository__init_instances):
  async def test_delete_existing_sensor(self):
    async with get_session() as session:
      sensor_id = self.sensor_ids[0]
      repo = SensorRepository(session)

      await repo.delete(sensor_id)
      await session.commit()

      deleted_sensor = await repo.get(sensor_id)
      self.assertIsNone(deleted_sensor)

  async def test_delete_non_existing_sensor(self):
    async with get_session() as session:
      repo = SensorRepository(session)

      with self.assertRaises(Exception):
        await repo.delete(999)  # Non-existing ID

  async def test_delete_device_cascades_delete_sensors(self):
    async with get_session() as session:
      device_id = self.device_ids[0]
      repo = SensorRepository(session)

      # Deletes Device
      smt = select(Device).where(Device.id == device_id)
      device = (await session.execute(smt)).first()[0]
      await session.delete(device)
      await session.commit()

      # Sensors must be deleted too
      sensor1 = await repo.get(self.sensor_ids[0])
      sensor2 = await repo.get(self.sensor_ids[1])

      self.assertIsNone(sensor1)
      self.assertIsNone(sensor2)
