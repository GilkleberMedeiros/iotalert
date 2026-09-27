"""
Test Base Model Repository.
"""

from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from typing import Set

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, delete

from app.models.base import BaseModel, ModelRepository
from test.conftest import InMemoryDatabaseTestCase, get_session

TZ_UTC = timezone.utc


class Store(BaseModel):
  __tablename__ = "test__store"

  name: Mapped[str]

  products: Mapped[Set[Product]] = relationship(
    back_populates="store", cascade="all, delete"
  )


class StoreRepository(ModelRepository[Store, dict, dict]):
  model = Store


class Product(BaseModel):
  __tablename__ = "test__product"

  name: Mapped[str]
  description: Mapped[str | None]
  price: Mapped[float]
  is_physical: Mapped[bool]
  tags: Mapped[str]
  store_id: Mapped[int] = mapped_column(
    ForeignKey("test__store.id", ondelete="CASCADE")
  )

  store: Mapped[Store] = relationship(back_populates="products")

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
    try:
      self.session_context = get_session()
      self.session = await self.session_context.__aenter__()

      await self._add_stores()
      await self._add_products()
    except Exception as e:
      await self.session_context.__aexit__(type(e), e, e.__traceback__)
      raise

  async def asyncTearDown(self):
    try:
      # Delete Products
      smt = delete(Product)
      await self.session.execute(smt)

      # Delete stores
      smt = delete(Store)
      await self.session.execute(smt)
      await self.session.commit()
      # await self.session.close()

    except Exception as e:
      await self.session_context.__aexit__(type(e), e, e.__traceback__)
      raise
    finally:
      await self.session_context.__aexit__(None, None, None)

    return await super().asyncTearDown()

  async def _add_stores(self):
    repo = StoreRepository(self.session)

    store_data = [{"name": "Store 1"}, {"name": "Store 2"}]

    stores = await repo.create(store_data)
    if not isinstance(stores, list):
      stores = [stores]

    await self.session.flush()  # Ensure the stores are persisted in the session
    self.store_ids = [store.id for store in stores]

  async def _add_products(self):
    self.repo = ProductRepository(self.session)

    product_data = [
      {
        "name": "Product 1",
        "description": "Description 1",
        "price": 1200.00,
        "is_physical": True,
        "tags": "",
        "store_id": self.store_ids[0],
      },
      {
        "name": "Product 2",
        "price": 799.99,
        "is_physical": False,
        "tags": "tag1, tag2",
        "store_id": self.store_ids[0],
      },
      {
        "name": "Product 3",
        "price": 59.99,
        "is_physical": True,
        "tags": "tag1",
        "store_id": self.store_ids[1],
      },
    ]

    products = await self.repo.create(product_data)
    if not isinstance(products, list):
      products = [products]

    await self.session.flush()  # Ensure the products are persisted in the session
    self.product_ids = [product.id for product in products]


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

  async def test_get_model_include_related(self):
    id = self.product_ids[1]

    product = await self.repo.get(id, [Product.store])

    self.assertIsInstance(product, Product)
    self.assertEqual(product.name, "Product 2")
    self.assertIsInstance(product.store, Store)
    self.assertEqual(product.store.name, "Store 1")


class TestModelRepository__list(TestModelRepository__init_instances):
  async def test_list_models(self):
    products = (await self.repo.list()).all()

    self.assertIsInstance(products, list)
    self.assertEqual(len(products), 3)
    self.assertEqual(products[0].name, "Product 1")
    self.assertEqual(products[1].name, "Product 2")
    self.assertEqual(products[2].name, "Product 3")

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
    self.assertEqual(len(products), 2)
    self.assertEqual(products[0].name, "Product 2")
    self.assertEqual(products[1].name, "Product 3")

  async def test_list_pagination_limit(self):
    products = (await self.repo.list({"limit": 1})).all()

    self.assertIsInstance(products, list)
    self.assertEqual(len(products), 1)
    self.assertEqual(products[0].name, "Product 1")

  async def test_list_models_include_related(self):
    products = (await self.repo.list(preload_related=[Product.store])).all()

    self.assertIsInstance(products, list)
    self.assertEqual(len(products), 3)
    self.assertEqual(products[0].name, "Product 1")
    self.assertIsInstance(products[0].store, Store)
    self.assertEqual(products[0].store.name, "Store 1")


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


class TestModelRepository__preload_related(TestModelRepository__init_instances):
  async def test_preload_related(self):
    smt_mock = MagicMock()
    arg1 = Product.store

    with patch("app.models.base.selectinload") as select_mock:
      smt_mock2 = ProductRepository._preload_related(smt_mock, [arg1])

      select_mock.assert_called_once_with(arg1)
      smt_mock.options.assert_called_with(select_mock(arg1))
      # Verify smt = smt.options(selectinload(p)) (assignment)
      self.assertEqual(smt_mock2, smt_mock.options(select_mock(arg1)))

  async def test_ignore_duplicates(self):
    smt_mock = MagicMock()

    ProductRepository._preload_related(smt_mock, [Product.store, Product.store])

    smt_mock.options.assert_called_once()

  async def test_related_empty(self):
    smt_mock = MagicMock()

    ProductRepository._preload_related(smt_mock, [])

    smt_mock.options.assert_not_called()
