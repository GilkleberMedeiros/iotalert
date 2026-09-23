import uuid

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.main import app
from app.models.sensor import Sensor, SensorRepository, CreateSensorData
from test.conftest import get_session
from test.api.test_devices import InitDevicesFixture


api_client = TestClient(app, base_url="http://testserver/sensors")


class InitSensorsFixture(InitDevicesFixture):
  async def asyncSetUp(self):
    setup = await super().asyncSetUp()

    async with get_session() as session:
      sensors_data: CreateSensorData = [
        {
          "device_id": self.devices_ids[0],
          "presentation_name": "Consumo",
          "key_name": "consumo",
          "unit": "kilowatt-hour",
        },
        {
          "device_id": self.devices_ids[0],
          "presentation_name": "Temperatura",
          "key_name": "temperatura",
          "unit": "fahrenheit",
        },
        {
          "device_id": self.devices_ids[1],
          "presentation_name": "Porcentagem de Gás na caixa do Transformador",
          "key_name": "gas_transformador",
          "unit": "percentage",
        },
      ]
      repo = SensorRepository(session)
      sensors: list[Sensor] = await repo.create(sensors_data)
      await session.commit()
      self.sensors_ids = [s.id for s in sensors]

    return setup

  async def asyncTearDown(self):
    async with get_session() as session:
      smt = delete(Sensor)
      await session.execute(smt)

    return await super().asyncTearDown()


class TestSensorsEndpointTestCase__create(InitDevicesFixture):
  async def test_can_create_sensor(self):
    sensor_data = {
      "device_id": str(self.devices_ids[0]),
      "presentation_name": "Consumo",
      "key_name": "consumo",
      "unit": "kilowatt-hour",
    }

    response = api_client.post(url="", json=sensor_data)
    status_code = response.status_code

    self.assertEqual(status_code, 201)
    sensor = response.json()
    self.assertIsInstance(sensor, dict)
    self.assertIsNotNone(sensor.get("id", None))
    self.assertEqual(sensor["device_id"], sensor_data["device_id"])
    self.assertEqual(sensor["presentation_name"], sensor_data["presentation_name"])
    self.assertEqual(sensor["key_name"], sensor_data["key_name"])
    self.assertEqual(sensor["unit"], sensor_data["unit"])
    self.assertIsNotNone(sensor.get("created_at", None))

  async def test_cant_create_sensor_with_empty_data(self):
    # Presentation Name Empty

    sensor_data1 = {
      "device_id": str(self.devices_ids[0]),
      "presentation_name": "",
      "key_name": "consumo",
      "unit": "kilowatt-hour",
    }

    response1 = api_client.post(url="", json=sensor_data1)
    status_code1 = response1.status_code

    self.assertEqual(status_code1, 400)
    content1 = response1.json()
    self.assertIsNotNone(content1.get("detail", None))

    # Key Name Empty

    sensor_data2 = {
      "device_id": str(self.devices_ids[0]),
      "presentation_name": "Consumo",
      "key_name": "",
      "unit": "kilowatt-hour",
    }

    response2 = api_client.post(url="", json=sensor_data2)
    status_code2 = response2.status_code

    self.assertEqual(status_code2, 400)
    content2 = response2.json()
    self.assertIsNotNone(content2.get("detail", None))

    # Unit Empty

    sensor_data3 = {
      "device_id": str(self.devices_ids[0]),
      "presentation_name": "Consumo",
      "key_name": "consumo",
      "unit": "",
    }

    response3 = api_client.post(url="", json=sensor_data3)
    status_code3 = response3.status_code

    self.assertEqual(status_code3, 422)
    content3 = response3.json()
    self.assertIsNotNone(content3.get("detail", None))

    # Device Id Empty

    sensor_data4 = {
      "device_id": "",
      "presentation_name": "Consumo",
      "key_name": "consumo",
      "unit": "kilowatt-hour",
    }

    response4 = api_client.post(url="", json=sensor_data4)
    status_code4 = response4.status_code

    self.assertEqual(status_code4, 422)
    content4 = response4.json()
    self.assertIsNotNone(content4.get("detail", None))

  async def test_cant_create_sensor_without_device_id(self):
    sensor_data = {
      "presentation_name": "Consumo",
      "key_name": "consumo",
      "unit": "kilowatt-hour",
    }

    response = api_client.post(url="", json=sensor_data)
    status_code = response.status_code

    self.assertEqual(status_code, 422)
    content = response.json()
    self.assertIsNotNone(content.get("detail", None))

  async def test_cant_create_sensor_with_inexistent_device_id(self):
    sensor_data = {
      "device_id": str(uuid.uuid4()),
      "presentation_name": "Consumo",
      "key_name": "consumo",
      "unit": "kilowatt-hour",
    }

    response = api_client.post(url="", json=sensor_data)
    status_code = response.status_code

    self.assertEqual(status_code, 404)
    content = response.json()
    self.assertIsNotNone(content.get("detail", None))

  async def test_cant_create_sensor_with_invalid_unit(self):
    sensor_data = {
      "device_id": str(self.devices_ids[0]),
      "presentation_name": "Consumo",
      "key_name": "consumo",
      "unit": "invalid-unit",
    }

    response = api_client.post("", json=sensor_data)
    status_code = response.status_code

    self.assertEqual(status_code, 422)
    content = response.json()
    self.assertIsNotNone(content.get("detail", None))


class TestSensorsEndpointTestCase__get(InitSensorsFixture):
  async def test_can_get_sensor(self):
    sensor_id = self.sensors_ids[0]

    response = api_client.get(url=f"/{sensor_id}")
    status_code = response.status_code

    self.assertEqual(status_code, 200)
    sensor = response.json()
    self.assertIsInstance(sensor, dict)
    self.assertEqual(sensor["id"], self.sensors_ids[0])
    self.assertEqual(sensor["device_id"], str(self.devices_ids[0]))
    self.assertEqual(sensor["presentation_name"], "Consumo")
    self.assertEqual(sensor["key_name"], "consumo")
    self.assertEqual(sensor["unit"], "kilowatt-hour")
    self.assertIsNotNone(sensor.get("created_at", None))

  async def test_cant_get_inexistent_sensor(self):
    sensor_id = 10_001

    response = api_client.get(url=f"/{sensor_id}")
    status_code = response.status_code

    self.assertEqual(status_code, 404)
    content = response.json()
    self.assertIsInstance(content, dict)
    self.assertIsNotNone(content.get("detail", None))


class TestSensorsEndpointTestCase__list(InitSensorsFixture):
  async def test_can_list_sensors(self):

    response = api_client.get("")
    status_code = response.status_code

    self.assertEqual(status_code, 200)
    sensors = response.json()
    self.assertIsInstance(sensors, list)
    self.assertEqual(len(sensors), 3)
    self.assertEqual(sensors[0]["id"], self.sensors_ids[0])
    self.assertEqual(sensors[1]["id"], self.sensors_ids[1])
    self.assertEqual(sensors[2]["id"], self.sensors_ids[2])

  async def test_list_empty_sensors(self):
    async with get_session() as session:
      smt = delete(table=Sensor)
      await session.execute(smt)

    response = api_client.get("")
    status_code = response.status_code

    self.assertEqual(status_code, 200)
    sensors = response.json()
    self.assertIsInstance(sensors, list)
    self.assertEqual(len(sensors), 0)

  async def test_list_sensors_paginated(self):
    response = api_client.get("?offset=1")
    status_code = response.status_code

    self.assertEqual(status_code, 200)
    sensors = response.json()
    self.assertIsInstance(sensors, list)
    self.assertEqual(len(sensors), 2)
    self.assertEqual(sensors[0]["id"], self.sensors_ids[1])
    self.assertEqual(sensors[1]["id"], self.sensors_ids[2])


class TestSensorsEndpointTestCase__update(InitSensorsFixture):
  async def test_can_update_sensor(self):
    sensor_id = self.sensors_ids[0]
    update_data = {"presentation_name": "Updated Present Name"}

    response = api_client.patch(f"/{sensor_id}", json=update_data)
    status_code = response.status_code

    self.assertEqual(status_code, 200)
    sensor = response.json()
    self.assertEqual(sensor["id"], sensor_id)
    self.assertEqual(sensor["presentation_name"], update_data["presentation_name"])

  async def test_cant_update_inexistent_sensor(self):
    sensor_id = 10_001
    update_data = {"presentation_name": "Updated Present Name"}

    response = api_client.patch(f"/{sensor_id}", json=update_data)
    status_code = response.status_code

    self.assertEqual(status_code, 404)
    content = response.json()
    self.assertIsInstance(content, dict)
    self.assertIsNotNone(content.get("detail", None))

  async def test_cant_update_sensor_with_empty_strings(self):
    sensor_id = str(self.sensors_ids[0])

    # Empty Presentation Name

    update_data1 = {"presentation_name": ""}

    response1 = api_client.patch(f"/{sensor_id}", json=update_data1)
    status_code1 = response1.status_code

    self.assertEqual(status_code1, 400)
    content1 = response1.json()
    self.assertIsInstance(content1, dict)
    self.assertIsNotNone(content1.get("detail", None))

    # Empty Key Name

    update_data2 = {"key_name": ""}

    response2 = api_client.patch(f"/{sensor_id}", json=update_data2)
    status_code2 = response2.status_code

    self.assertEqual(status_code2, 400)
    content2 = response2.json()
    self.assertIsInstance(content2, dict)
    self.assertIsNotNone(content2.get("detail", None))

    # Empty Unit

    update_data3 = {"unit": ""}

    response3 = api_client.patch(f"/{sensor_id}", json=update_data3)
    status_code3 = response3.status_code

    self.assertEqual(status_code3, 422)
    content3 = response3.json()
    self.assertIsInstance(content3, dict)
    self.assertIsNotNone(content3.get("detail", None))

    # Empty Device Id

    update_data4 = {"unit": ""}

    response4 = api_client.patch(f"/{sensor_id}", json=update_data4)
    status_code4 = response4.status_code

    self.assertEqual(status_code4, 422)
    content4 = response4.json()
    self.assertIsInstance(content4, dict)
    self.assertIsNotNone(content4.get("detail", None))

  async def test_can_update_sensor_device(self):
    sensor_id = self.sensors_ids[0]
    update_data = {
      "presentation_name": "Updated Present Name",
      "device_id": str(self.devices_ids[1]),
    }

    response = api_client.patch(f"/{sensor_id}", json=update_data)
    status_code = response.status_code

    self.assertEqual(status_code, 200)
    content = response.json()
    self.assertIsInstance(content, dict)
    self.assertEqual(content.get("presentation_name"), "Updated Present Name")
    self.assertEqual(content.get("device_id"), str(self.devices_ids[1]))

  async def test_cant_update_sensor_device_with_inexistent_device(self):
    sensor_id = self.sensors_ids[0]
    update_data = {
      "presentation_name": "Updated Present Name",
      "device_id": str(self.devices_ids[1]),
    }

    response = api_client.patch(f"/{sensor_id}", json=update_data)
    status_code = response.status_code

    self.assertEqual(status_code, 200)
    content = response.json()
    self.assertIsInstance(content, dict)
    self.assertEqual(content.get("presentation_name"), "Updated Present Name")
    self.assertEqual(content.get("device_id"), str(self.devices_ids[1]))


class TestSensorsEndpointTestCase__delete(InitSensorsFixture):
  async def test_can_delete(self):
    sensor_id = self.sensors_ids[0]

    response = api_client.delete(url=f"/{sensor_id}")
    status_code = response.status_code

    self.assertEqual(status_code, 200)
    content = response.json()
    self.assertIsInstance(content, dict)
    self.assertIsNotNone(content.get("detail", None))
    self.assertEqual(content.get("success", None), True)

    # Verify on database
    async with get_session() as session:
      repo = SensorRepository(session)
      sensor = await repo.get(sensor_id)
      self.assertIsNone(sensor)

  async def test_cant_delete_inexistent_sensor(self):
    sensor_id = 10_001

    response = api_client.delete(url=f"/{sensor_id}")
    status_code = response.status_code

    self.assertEqual(status_code, 404)
    content = response.json()
    self.assertIsInstance(content, dict)
    self.assertIsNotNone(content.get("detail", None))
