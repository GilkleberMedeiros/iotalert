from datetime import datetime

from app.db import get_session
from app.models.sensor import (
  Sensor,
  SensorRepository,
)
from test.conftest import InMemoryDatabaseTestCase


class TestSensorRepository__init_instances(InMemoryDatabaseTestCase):
  def setUp(self):
    with next(get_session()) as session:
      self.repo = SensorRepository(session)

      sensor_data = [
        {"presentation_name": "Sensor 1", "key_name": "sensor_1", "unit": "celsius"},
        {"presentation_name": "Sensor 2", "key_name": "sensor_2", "unit": "degree"},
      ]

      sensors = self.repo.create(sensor_data)
      session.commit()  # Ensure the sensors are persisted in the session
      self.sensor_ids = [sensor.id for sensor in sensors]

    return super().setUp()

  def tearDown(self):
    with next(get_session()) as session:
      session.query(Sensor).delete()
      session.commit()

    return super().tearDown()


class TestSensorRepository_create(InMemoryDatabaseTestCase):
  def test_create_single_sensor(self):
    with next(get_session()) as session:
      repo = SensorRepository(session)

      sensor_data = {
        "presentation_name": "Test Sensor",
        "key_name": "test_name",
        "unit": "celsius",
      }

      sensor = repo.create(sensor_data)
      session.commit()  # Commit the session to persist the changes

      self.assertIsInstance(sensor, Sensor)
      self.assertIsNotNone(sensor.id)
      self.assertEqual(sensor.presentation_name, sensor_data["presentation_name"])
      self.assertEqual(sensor.key_name, sensor_data["key_name"])
      # Should set status as ACTIVE by default
      self.assertEqual(sensor.unit.name, "celsius")
      self.assertIsInstance(sensor.created_at, datetime)

  def test_create_multiple_sensors(self):
    with next(get_session()) as session:
      repo = SensorRepository(session)

      sensors_data = [
        {
          "presentation_name": "Test Sensor 1",
          "key_name": "test_name_1",
          "unit": "celsius",
        },
        {
          "presentation_name": "Test Sensor 2",
          "key_name": "test_name_2",
          "unit": "kelvin",
        },
      ]

      sensors = repo.create(sensors_data)
      session.commit()  # Commit the session to persist the changes

      self.assertIsInstance(sensors, list)
      self.assertEqual(len(sensors), 2)
      self.assertIsInstance(sensors[0], Sensor)
      self.assertIsInstance(sensors[1], Sensor)
      self.assertEqual(
        sensors[0].presentation_name, sensors_data[0]["presentation_name"]
      )
      self.assertEqual(
        sensors[1].presentation_name, sensors_data[1]["presentation_name"]
      )

  def test_create_sensor_with_empty_strings_raises_value_error(self):
    with next(get_session()) as session:
      repo = SensorRepository(session)

      sensor_data1 = {
        "presentation_name": "",  # Empty presentation_name
        "key_name": "test_key_name",
        "unit": "kelvin",
      }

      with self.assertRaises(ValueError):
        repo.create(sensor_data1)

      sensor_data2 = {
        "presentation_name": "Test Presentation Name",
        "key_name": "",  # Empty key_name
        "unit": "percentage",
      }

      with self.assertRaises(ValueError):
        repo.create(sensor_data2)

      sensor_data3 = {
        "presentation_name": "Test Presentation Name",
        "key_name": "test_key_name",
        "unit": "",  # Empty unit
      }

      with self.assertRaises(ValueError):
        repo.create(sensor_data3)

  def test_create_sensor_with_invalid_key_name(self):
    with next(get_session()) as session:
      repo = SensorRepository(session)

      sensor_data = {
        "presentation_name": "Test Name",
        "key_name": "^key name$",
        "unit": "degree",
      }

      with self.assertRaises(ValueError):
        repo.create(sensor_data)

  def test_create_sensor_with_invalid_unit(self):
    with next(get_session()) as session:
      repo = SensorRepository(session)

      sensor_data = {
        "presentation_name": "Test Name",
        "key_name": "test_key_name",
        "unit": "<unknow_unit>",
      }

      with self.assertRaises(ValueError):
        repo.create(sensor_data)


class TestSensorRepository_get(TestSensorRepository__init_instances):
  def test_get_existing_sensor(self):
    with next(get_session()) as session:
      sensor_id = self.sensor_ids[0]
      repo = SensorRepository(session)

      # Get the first sensor created in setUp
      sensor = repo.get(sensor_id)

      self.assertIsInstance(sensor, Sensor)
      self.assertEqual(sensor.id, sensor_id)
      self.assertEqual(sensor.presentation_name, "Sensor 1")
      self.assertEqual(sensor.key_name, "sensor_1")
      self.assertEqual(sensor.unit.name, "celsius")

  def test_get_non_existing_sensor(self):
    with next(get_session()) as session:
      repo = SensorRepository(session)

      sensor = repo.get(999)  # Non-existing ID

      self.assertIsNone(sensor)


class TestSensorRepository__list(TestSensorRepository__init_instances):
  def test_list_sensors(self):
    with next(get_session()) as session:
      repo = SensorRepository(session)

      sensors = repo.list().all()

      self.assertIsInstance(sensors, list)
      self.assertEqual(len(sensors), 2)
      self.assertIsInstance(sensors[0], Sensor)
      self.assertIsInstance(sensors[1], Sensor)

  def test_list_empty(self):
    with next(get_session()) as session:
      # Clear all sensors first
      session.query(Sensor).delete()
      session.commit()

      repo = SensorRepository(session)

      sensors = repo.list().all()

      self.assertIsInstance(sensors, list)
      self.assertEqual(len(sensors), 0)


class TestSensorRepository__update(TestSensorRepository__init_instances):
  def test_update_existing_sensor(self):
    with next(get_session()) as session:
      sensor_id = self.sensor_ids[0]
      repo = SensorRepository(session)

      update_data = {
        "presentation_name": "Updated Sensor Name",
        "key_name": "updated_keyname",
        "unit": "kilowatt",
      }

      updated_sensor = repo.update(sensor_id, update_data)
      session.commit()

      self.assertIsInstance(updated_sensor, Sensor)
      self.assertEqual(updated_sensor.id, sensor_id)
      self.assertEqual(
        updated_sensor.presentation_name, update_data["presentation_name"]
      )
      self.assertEqual(updated_sensor.key_name, update_data["key_name"])
      self.assertEqual(updated_sensor.unit.name, update_data["unit"])

  def test_update_non_existing_sensor(self):
    with next(get_session()) as session:
      repo = SensorRepository(session)

      update_data = {
        "presentation_name": "Non-existing Sensor",
        "key_name": "some_key",
        "unit": "kilowatt-hour",
      }

      with self.assertRaises(Exception):
        repo.update(999, update_data)  # Non-existing ID

  def test_update_cant_update_id(self):
    with next(get_session()) as session:
      sensor_id = self.sensor_ids[0]
      repo = SensorRepository(session)

      update_data = {
        "id": "new_id",
      }

      updated_sensor = repo.update(sensor_id, update_data)
      session.commit()

      self.assertEqual(updated_sensor.id, sensor_id)  # ID should not change

  def test_update_with_invalid_unit_raises_value_error(self):
    with next(get_session()) as session:
      sensor_id = self.sensor_ids[0]
      repo = SensorRepository(session)

      update_data = {
        "unit": "invalid-unit",  # Invalid unit
      }

      with self.assertRaises(ValueError):
        repo.update(sensor_id, update_data)

  def test_update_with_invalid_key_name_raises_value_error(self):
    with next(get_session()) as session:
      sensor_id = self.sensor_ids[0]
      repo = SensorRepository(session)

      update_data = {"key_name": "Invalid KeyName"}

      with self.assertRaises(ValueError):
        repo.update(sensor_id, update_data)

  def test_update_fields_to_empty_strings(self):
    with next(get_session()) as session:
      sensor_id = self.sensor_ids[1]
      repo = SensorRepository(session)

      update_data = {"presentation_name": ""}

      with self.assertRaises(ValueError):
        repo.update(sensor_id, update_data)

      update_data2 = {"key_name": ""}

      with self.assertRaises(ValueError):
        repo.update(sensor_id, update_data2)

      update_data3 = {"unit": ""}

      with self.assertRaises(ValueError):
        repo.update(sensor_id, update_data3)

  def test_update_cant_update_created_at(self):
    with next(get_session()) as session:
      sensor_id = self.sensor_ids[0]
      repo = SensorRepository(session)

      update_data = {"created_at": datetime.now()}

      with self.assertRaises(ValueError):
        repo.update(sensor_id, update_data)


class TestSensorRepository__delete(TestSensorRepository__init_instances):
  def test_delete_existing_sensor(self):
    with next(get_session()) as session:
      sensor_id = self.sensor_ids[0]
      repo = SensorRepository(session)

      repo.delete(sensor_id)
      session.commit()

      deleted_sensor = repo.get(sensor_id)
      self.assertIsNone(deleted_sensor)

  def test_delete_non_existing_sensor(self):
    with next(get_session()) as session:
      repo = SensorRepository(session)

      with self.assertRaises(Exception):
        repo.delete(999)  # Non-existing ID
