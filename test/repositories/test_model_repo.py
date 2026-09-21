"""
Test Base Model Repository.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import delete

from app.models.base import BaseModel, ModelRepository
from test.conftest import InMemoryDatabaseTestCase, get_session

TZ_UTC = timezone.utc


class Product(BaseModel):
  __tablename__ = "test__product"

  name: Mapped[str]
  description: Mapped[str | None]
  price: Mapped[float]
  is_physical: Mapped[bool]
  tags: Mapped[str]

  created_at: Mapped[datetime] = mapped_column(
    nullable=False, default=lambda: datetime.now(TZ_UTC)
  )
  updated_at: Mapped[datetime] = mapped_column(
    nullable=False,
    default=lambda: datetime.now(TZ_UTC),
    onupdate=lambda: datetime.now(TZ_UTC),
  )


class ProductRepository(ModelRepository[Product, dict, dict]):
  model = Product


class TestModelRepository__init_instances(InMemoryDatabaseTestCase):
  async def asyncSetUp(self):
    await super().asyncSetUp()
    async with get_session() as session:
      self.repo = ProductRepository(session)

      product_data = [
        {
          "name": "Product 1",
          "description": "Description 1",
          "price": 1200.00,
          "is_physical": True,
          "tags": "",
        },
        {
          "name": "Product 2",
          "price": 799.99,
          "is_physical": False,
          "tags": "tag1, tag2",
        },
      ]

      products = await self.repo.create(product_data)
      if not isinstance(products, list):
        products = [products]
      await session.commit()  # Ensure the products are persisted in the session
      self.product_ids = [product.id for product in products]

  async def asyncTearDown(self):
    async with get_session() as session:
      smt = delete(Product)
      await session.execute(smt)
      await session.commit()

    return await super().asyncTearDown()


class TestModelRepository__create(InMemoryDatabaseTestCase):
  async def test_bulk_create(self):
    async with get_session() as session:
      repo = ProductRepository(session)

      product_data = [
        {
          "name": "Product 1",
          "description": "Description 1",
          "price": 1200.00,
          "is_physical": True,
          "tags": "",
        },
        {
          "name": "Product 2",
          "price": 799.99,
          "is_physical": False,
          "tags": "tag1, tag2",
        },
      ]

      result = await repo.create(product_data)

      self.assertIsInstance(result, list)
      self.assertEqual(len(result), 2)
      self.assertEqual(result[0].name, "Product 1")
      self.assertEqual(result[1].name, "Product 2")

  async def test_single_create(self):
    async with get_session() as session:
      repo = ProductRepository(session)

      product_data = {
        "name": "Product 1",
        "description": "Description 1",
        "price": 1200.00,
        "is_physical": True,
        "tags": "",
      }

      product = await repo.create(product_data)

      self.assertIsInstance(product, Product)
      self.assertEqual(product.name, "Product 1")


class TestModelRepository__get(TestModelRepository__init_instances):
  async def test_get_existent_model(self):
    id = self.product_ids[0]

    product = await self.repo.get(id)

    self.assertIsInstance(product, Product)
    self.assertEqual(product.name, "Product 1")

  async def test_get_inexistent_model(self):
    id = 1001

    product = await self.repo.get(id)

    self.assertIsNone(product)


class TestModelRepository__list(TestModelRepository__init_instances):
  async def test_list_models(self):
    products = (await self.repo.list()).all()

    self.assertIsInstance(products, list)
    self.assertEqual(len(products), 2)
    self.assertEqual(products[0].name, "Product 1")
    self.assertEqual(products[1].name, "Product 2")

  async def test_list_empty(self):
    async with get_session() as session:
      smt = delete(Product)
      await session.execute(smt)

      products = (await self.repo.list()).all()

      self.assertIsInstance(products, list)
      self.assertEqual(len(products), 0)

  async def test_list_pagination_offset(self):
    products = (await self.repo.list({"offset": 1})).all()

    self.assertIsInstance(products, list)
    self.assertEqual(len(products), 1)
    self.assertEqual(products[0].name, "Product 2")

  async def test_list_pagination_limit(self):
    products = (await self.repo.list({"limit": 1})).all()

    self.assertIsInstance(products, list)
    self.assertEqual(len(products), 1)
    self.assertEqual(products[0].name, "Product 1")


class TestModelRepository__update(TestModelRepository__init_instances):
  async def test_update_model(self):
    id = self.product_ids[0]
    update_data = {
      "name": "Updated 1",
      "description": "Updated description 1",
      "price": 1199.90,
      "is_physical": True,
      "tags": "updated",
    }

    updated = await self.repo.update(id, update_data)

    self.assertIsInstance(updated, Product)
    self.assertEqual(updated.name, "Updated 1")
    self.assertEqual(updated.description, "Updated description 1")
    self.assertEqual(updated.price, 1199.90)
    self.assertEqual(updated.is_physical, True)
    self.assertEqual(updated.tags, "updated")

  async def test_update_raises_error_for_inexistent_model(self):
    id = 10_001
    update_data = {
      "name": "Updated 1",
      "description": "Updated description 1",
      "price": 1199.90,
      "is_physical": True,
      "tags": "updated",
    }

    with self.assertRaises(Exception):
      await self.repo.update(id, update_data)

  async def test_update_partial(self):
    id = self.product_ids[1]
    update_data = {
      "name": "Updated 2",
    }

    updated = await self.repo.update(id, update_data)

    self.assertIsInstance(updated, Product)
    self.assertEqual(updated.name, "Updated 2")

  async def test_update_cant_update_id(self):
    id = self.product_ids[1]
    update_data = {
      "id": id + 1,
      "name": "Updated 2",
    }

    updated = await self.repo.update(id, update_data)

    self.assertIsInstance(updated, Product)
    self.assertNotEqual(updated.id, id + 1)
    self.assertEqual(updated.id, id)
    self.assertEqual(updated.name, "Updated 2")


class TestModelRepository__delete(TestModelRepository__init_instances):
  async def test_delete_model(self):
    id = self.product_ids[0]

    await self.repo.delete(id)
    product = await self.repo.get(id)

    self.assertIsNone(product)

  async def test_delete_raises_error_for_inexistent_model(self):
    id = 10_001

    with self.assertRaises(Exception):
      await self.repo.delete(id)
