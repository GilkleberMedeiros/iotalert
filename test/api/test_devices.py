import uuid

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.main import app
from app.models.device import Device, DeviceRepository
from test.conftest import InMemoryDatabaseTestCase, get_session


api_client = TestClient(app, base_url="http://testserver/devices")


class InitDevicesFixture(InMemoryDatabaseTestCase):
  async def asyncSetUp(self):
    setup = await super().asyncSetUp()

    async with get_session() as session:
      devices_data = [
        {"name": "Device 1", "location": "Test Location 1"},
        {"name": "Device 2", "location": "Test Location 2", "status": "inactive"},
      ]
      repo = DeviceRepository(session)
      devices: list[Device] = await repo.create(devices_data)
      await session.commit()
      self.devices_ids = [d.id for d in devices]

    return setup

  async def asyncTearDown(self):
    async with get_session() as session:
      smt = delete(Device)
      await session.execute(smt)

    return await super().asyncTearDown()


class TestDevicesEndpointTestCase__create(InMemoryDatabaseTestCase):
  async def test_can_create_device(self):
    device_data = {"name": "Device 1", "location": "Test Location 1"}

    response = api_client.post(url="", json=device_data)
    status_code = response.status_code

    self.assertEqual(status_code, 201)
    device = response.json()
    self.assertIsInstance(device, dict)
    self.assertIsNotNone(device.get("id", None))
    self.assertEqual(device["name"], device_data["name"])
    self.assertEqual(device["location"], device_data["location"])
    self.assertEqual(device["status"], "active")
    self.assertIsNotNone(device.get("created_at", None))
    self.assertIsNotNone(device.get("updated_at", None))

  async def test_cant_create_device_with_empty_data(self):
    # Name Empty

    device_data1 = {"name": "", "location": "Test Location 1"}

    response1 = api_client.post(url="", json=device_data1)
    status_code1 = response1.status_code

    self.assertEqual(status_code1, 400)
    content1 = response1.json()
    self.assertIsNotNone(content1.get("detail", None))

    # Location Empty

    device_data2 = {"name": "Test Name", "location": ""}

    response2 = api_client.post(url="", json=device_data2)
    status_code2 = response2.status_code

    self.assertEqual(status_code2, 400)
    content2 = response2.json()
    self.assertIsNotNone(content2.get("detail", None))

    # Status Empty

    device_data3 = {"name": "Test Name", "location": "Test Location", "status": ""}

    response3 = api_client.post(url="", json=device_data3)
    status_code3 = response3.status_code

    self.assertEqual(status_code3, 422)
    content3 = response3.json()
    self.assertIsNotNone(content3.get("detail", None))

  async def test_cant_create_device_with_anomaly_status(self):
    device_data = {
      "name": "Test Name",
      "location": "Test Location",
      "status": Device.Status["ANOMALY"].value,
    }

    response = api_client.post("", json=device_data)
    status_code = response.status_code

    self.assertEqual(status_code, 422)
    content = response.json()
    self.assertIsNotNone(content.get("detail", None))

  async def test_can_create_device_with_given_status(self):
    device_data = {
      "name": "Test Name",
      "location": "Test Location",
      "status": Device.Status["INACTIVE"].value,
    }

    response = api_client.post("", json=device_data)
    status_code = response.status_code

    self.assertEqual(status_code, 201)
    device = response.json()
    self.assertIsInstance(device, dict)
    self.assertEqual(device["name"], device_data["name"])
    self.assertEqual(device["status"], device_data["status"])

  async def test_cant_create_device_with_invalid_status(self):
    device_data = {
      "name": "Test Name",
      "location": "Test Location",
      "status": "invalid_status",
    }

    response = api_client.post("", json=device_data)
    status_code = response.status_code

    self.assertEqual(status_code, 422)
    content = response.json()
    self.assertIsNotNone(content.get("detail", None))


class TestDevicesEndpointTestCase__get(InitDevicesFixture):
  async def test_can_get_device(self):
    device_id = str(self.devices_ids[0])

    response = api_client.get(url=f"/{device_id}")
    status_code = response.status_code

    self.assertEqual(status_code, 200)
    device = response.json()
    self.assertIsInstance(device, dict)
    self.assertEqual(device["id"], device_id)
    self.assertEqual(device["name"], "Device 1")
    self.assertEqual(device["location"], "Test Location 1")
    self.assertEqual(device["status"], "active")
    self.assertIsNotNone(device.get("created_at", None))
    self.assertIsNotNone(device.get("updated_at", None))

  async def test_cant_get_inexistent_device(self):
    device_id = uuid.uuid4()

    response = api_client.get(url=f"/{device_id}")
    status_code = response.status_code

    self.assertEqual(status_code, 404)
    content = response.json()
    self.assertIsInstance(content, dict)
    self.assertIsNotNone(content.get("detail", None))


class TestDevicesEndpointTestCase__list(InitDevicesFixture):
  async def test_can_list_devices(self):

    response = api_client.get("")
    status_code = response.status_code

    self.assertEqual(status_code, 200)
    devices = response.json()
    self.assertIsInstance(devices, list)
    self.assertEqual(len(devices), 2)
    self.assertEqual(devices[0]["id"], str(self.devices_ids[0]))
    self.assertEqual(devices[1]["id"], str(self.devices_ids[1]))

  async def test_list_empty_devices(self):
    async with get_session() as session:
      smt = delete(Device)
      await session.execute(smt)

    response = api_client.get("")
    status_code = response.status_code

    self.assertEqual(status_code, 200)
    devices = response.json()
    self.assertIsInstance(devices, list)
    self.assertEqual(len(devices), 0)


class TestDevicesEndpointTestCase__update(InitDevicesFixture):
  async def test_can_update_device(self):
    device_id = str(self.devices_ids[0])
    update_data = {"name": "Updated Name"}

    response = api_client.patch(f"/{device_id}", json=update_data)
    status_code = response.status_code

    self.assertEqual(status_code, 200)
    device = response.json()
    self.assertEqual(device["id"], device_id)
    self.assertEqual(device["name"], update_data["name"])

  async def test_cant_update_inexistent_device(self):
    device_id = str(uuid.uuid4())
    update_data = {"name": "Updated Name"}

    response = api_client.patch(f"/{device_id}", json=update_data)
    status_code = response.status_code

    self.assertEqual(status_code, 404)
    content = response.json()
    self.assertIsInstance(content, dict)
    self.assertIsNotNone(content.get("detail", None))

  async def test_cant_update_device_with_empty_strings(self):
    device_id = str(self.devices_ids[0])

    # Empty Name

    update_data1 = {"name": ""}

    response1 = api_client.patch(f"/{device_id}", json=update_data1)
    status_code1 = response1.status_code

    self.assertEqual(status_code1, 400)
    content1 = response1.json()
    self.assertIsInstance(content1, dict)
    self.assertIsNotNone(content1.get("detail", None))

    # Empty Location

    update_data2 = {"location": ""}

    response2 = api_client.patch(f"/{device_id}", json=update_data2)
    status_code2 = response2.status_code

    self.assertEqual(status_code2, 400)
    content2 = response2.json()
    self.assertIsInstance(content2, dict)
    self.assertIsNotNone(content2.get("detail", None))

  async def test_cant_update_device_status(self):
    device_id = str(self.devices_ids[0])
    update_data = {"name": "Updated Name", "status": "inactive"}

    response = api_client.patch(f"/{device_id}", json=update_data)
    status_code = response.status_code

    self.assertEqual(status_code, 200)
    content = response.json()
    self.assertIsInstance(content, dict)
    self.assertEqual(content.get("name"), "Updated Name")
    self.assertEqual(content.get("status"), "active")  # Didn't change


class TestDevicesEndpointTestCase__delete(InitDevicesFixture):
  async def test_can_delete(self):
    device_id = str(self.devices_ids[0])

    response = api_client.delete(url=f"/{device_id}")
    status_code = response.status_code

    self.assertEqual(status_code, 200)
    content = response.json()
    self.assertIsInstance(content, dict)
    self.assertIsNotNone(content.get("detail", None))
    self.assertEqual(content.get("success", None), True)

    # Verify on database
    async with get_session() as session:
      repo = DeviceRepository(session)
      device = await repo.get(device_id)
      self.assertIsNone(device)

  async def test_cant_delete_inexistent_device(self):
    device_id = str(uuid.uuid4())

    response = api_client.delete(url=f"/{device_id}")
    status_code = response.status_code

    self.assertEqual(status_code, 404)
    content = response.json()
    self.assertIsInstance(content, dict)
    self.assertIsNotNone(content.get("detail", None))


class TestDevicesEndpointTestCase__activate(InitDevicesFixture):
  async def test_can_activate_device(self):
    device_id = self.devices_ids[1]

    response = api_client.patch(f"/activate/{device_id}")
    status_code = response.status_code

    self.assertEqual(status_code, 200)
    content = response.json()
    self.assertIsInstance(content, dict)
    self.assertIsNotNone(content.get("detail", None))

    # Verify on database
    async with get_session() as session:
      repo = DeviceRepository(session)
      device = await repo.get(device_id)

      self.assertIsNotNone(device)
      self.assertEqual(device.status.value, "active")

  async def test_can_activate_device_already_activated(self):
    device_id = self.devices_ids[0]

    response = api_client.patch(f"/activate/{device_id}")
    status_code = response.status_code

    self.assertEqual(status_code, 200)
    content = response.json()
    self.assertIsInstance(content, dict)
    self.assertIsNotNone(content.get("detail", None))

  async def test_cant_activate_inexistent_device(self):
    device_id = str(uuid.uuid4())

    response = api_client.patch(f"/activate/{device_id}")
    status_code = response.status_code

    self.assertEqual(status_code, 404)
    content = response.json()
    self.assertIsInstance(content, dict)
    self.assertIsNotNone(content.get("detail", None))


class TestDevicesEndpointTestCase__inactivate(InitDevicesFixture):
  async def test_can_inactivate_device(self):
    device_id = self.devices_ids[1]

    response = api_client.patch(f"/inactivate/{device_id}")
    status_code = response.status_code

    self.assertEqual(status_code, 200)
    content = response.json()
    self.assertIsInstance(content, dict)
    self.assertIsNotNone(content.get("detail", None))

    # Verify on database
    async with get_session() as session:
      repo = DeviceRepository(session)
      device = await repo.get(device_id)

      self.assertIsNotNone(device)
      self.assertEqual(device.status.value, "inactive")

  async def test_can_inactivate_device_already_inactivated(self):
    device_id = self.devices_ids[0]

    response = api_client.patch(f"/inactivate/{device_id}")
    status_code = response.status_code

    self.assertEqual(status_code, 200)
    content = response.json()
    self.assertIsInstance(content, dict)
    self.assertIsNotNone(content.get("detail", None))

  async def test_cant_inactivate_inexistent_device(self):
    device_id = str(uuid.uuid4())

    response = api_client.patch(f"/inactivate/{device_id}")
    status_code = response.status_code

    self.assertEqual(status_code, 404)
    content = response.json()
    self.assertIsInstance(content, dict)
    self.assertIsNotNone(content.get("detail", None))
