import pytest

from typing import Any, Mapping, Generator
from fastapi.testclient import TestClient
from main import app
from http import HTTPStatus


@pytest.fixture
def app_client() -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client

# Хороший продавец -> False
@pytest.mark.parametrize('seller_id', [1])
@pytest.mark.parametrize('is_verified_seller', [True])
@pytest.mark.parametrize('item_id', [1])
@pytest.mark.parametrize('name', ['test'])
@pytest.mark.parametrize('description', ['description'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [0])
def test_predict_good_seller(
    app_client: TestClient,
    seller_id: int,
    is_verified_seller: bool,
    item_id: int,
    name: str,
    description: str,
    category: int,
    images_qty: int
):
    data = {
        "seller_id":          seller_id,
        "is_verified_seller": is_verified_seller,
        "item_id":            item_id,
        "name":               name,
        "description":        description,
        "category":           category,
        "images_qty":         images_qty
    }
    
    response = app_client.post('/predict', json=data)
    assert response.status_code == HTTPStatus.OK
    assert response.json() is False

# Плохой продавец, но с картинками -> False
@pytest.mark.parametrize('seller_id', [1])
@pytest.mark.parametrize('is_verified_seller', [False])
@pytest.mark.parametrize('item_id', [1])
@pytest.mark.parametrize('name', ['test'])
@pytest.mark.parametrize('description', ['description'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [1])
def test_bad_seller_with_images(
    app_client: TestClient,
    seller_id: int,
    is_verified_seller: bool,
    item_id: int,
    name: str,
    description: str,
    category: int,
    images_qty: int
):
    data = {
        "seller_id":          seller_id,
        "is_verified_seller": is_verified_seller,
        "item_id":            item_id,
        "name":               name,
        "description":        description,
        "category":           category,
        "images_qty":         images_qty
    }
    
    response = app_client.post('/predict', json=data)
    assert response.status_code == HTTPStatus.OK
    assert response.json() is False

# Плохой продавец, без картинок -> True
@pytest.mark.parametrize('seller_id', [1])
@pytest.mark.parametrize('is_verified_seller', [False])
@pytest.mark.parametrize('item_id', [1])
@pytest.mark.parametrize('name', ['test'])
@pytest.mark.parametrize('description', ['description'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [0])
def test_bad_seller_without_images(
    app_client: TestClient,
    seller_id: int,
    is_verified_seller: bool,
    item_id: int,
    name: str,
    description: str,
    category: int,
    images_qty: int
):
    data = {
        "seller_id":          seller_id,
        "is_verified_seller": is_verified_seller,
        "item_id":            item_id,
        "name":               name,
        "description":        description,
        "category":           category,
        "images_qty":         images_qty
    }
    
    response = app_client.post('/predict', json=data)
    assert response.status_code == HTTPStatus.OK
    assert response.json() is True

# Тест на seller_id > 0
@pytest.mark.parametrize('seller_id', [0])
@pytest.mark.parametrize('is_verified_seller', [False])
@pytest.mark.parametrize('item_id', [1])
@pytest.mark.parametrize('name', ['test'])
@pytest.mark.parametrize('description', ['description'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [0])
def test_seller_id_zero(
    app_client: TestClient,
    seller_id: int,
    is_verified_seller: bool,
    item_id: int,
    name: str,
    description: str,
    category: int,
    images_qty: int
):
    data = {
        "seller_id":          seller_id,
        "is_verified_seller": is_verified_seller,
        "item_id":            item_id,
        "name":               name,
        "description":        description,
        "category":           category,
        "images_qty":         images_qty
    }
    
    response = app_client.post('/predict', json=data)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

# Тест на item_id > 0
@pytest.mark.parametrize('seller_id', [1])
@pytest.mark.parametrize('is_verified_seller', [False])
@pytest.mark.parametrize('item_id', [0])
@pytest.mark.parametrize('name', ['test'])
@pytest.mark.parametrize('description', ['description'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [0])
def test_item_id_zero(
    app_client: TestClient,
    seller_id: int,
    is_verified_seller: bool,
    item_id: int,
    name: str,
    description: str,
    category: int,
    images_qty: int
):
    data = {
        "seller_id":          seller_id,
        "is_verified_seller": is_verified_seller,
        "item_id":            item_id,
        "name":               name,
        "description":        description,
        "category":           category,
        "images_qty":         images_qty
    }
    
    response = app_client.post('/predict', json=data)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

# Проверка на пустоту name
@pytest.mark.parametrize('seller_id', [1])
@pytest.mark.parametrize('is_verified_seller', [False])
@pytest.mark.parametrize('item_id', [1])
@pytest.mark.parametrize('name', [''])
@pytest.mark.parametrize('description', ['description'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [0])
def test_empty_name(
    app_client: TestClient,
    seller_id: int,
    is_verified_seller: bool,
    item_id: int,
    name: str,
    description: str,
    category: int,
    images_qty: int
):
    data = {
        "seller_id":          seller_id,
        "is_verified_seller": is_verified_seller,
        "item_id":            item_id,
        "name":               name,
        "description":        description,
        "category":           category,
        "images_qty":         images_qty
    }
    
    response = app_client.post('/predict', json=data)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

# Проверка на макс. длину name
@pytest.mark.parametrize('seller_id', [1])
@pytest.mark.parametrize('is_verified_seller', [False])
@pytest.mark.parametrize('item_id', [1])
@pytest.mark.parametrize('name', ['*' * 257])
@pytest.mark.parametrize('description', ['description'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [0])
def test_long_name(
    app_client: TestClient,
    seller_id: int,
    is_verified_seller: bool,
    item_id: int,
    name: str,
    description: str,
    category: int,
    images_qty: int
):
    data = {
        "seller_id":          seller_id,
        "is_verified_seller": is_verified_seller,
        "item_id":            item_id,
        "name":               name,
        "description":        description,
        "category":           category,
        "images_qty":         images_qty
    }
    
    response = app_client.post('/predict', json=data)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

# Проверка на макс. длину description
@pytest.mark.parametrize('seller_id', [1])
@pytest.mark.parametrize('is_verified_seller', [False])
@pytest.mark.parametrize('item_id', [1])
@pytest.mark.parametrize('name', ['test'])
@pytest.mark.parametrize('description', ['a' * (2**14 + 1)])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [0])
def test_long_description(
    app_client: TestClient,
    seller_id: int,
    is_verified_seller: bool,
    item_id: int,
    name: str,
    description: str,
    category: int,
    images_qty: int
):
    data = {
        "seller_id":          seller_id,
        "is_verified_seller": is_verified_seller,
        "item_id":            item_id,
        "name":               name,
        "description":        description,
        "category":           category,
        "images_qty":         images_qty
    }
    
    response = app_client.post('/predict', json=data)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


# Проверка на не отриацтельное число images_qty
@pytest.mark.parametrize('seller_id', [1])
@pytest.mark.parametrize('is_verified_seller', [False])
@pytest.mark.parametrize('item_id', [1])
@pytest.mark.parametrize('name', ['test'])
@pytest.mark.parametrize('description', ['description'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [-1])
def test_negative_images_qty(
    app_client: TestClient,
    seller_id: int,
    is_verified_seller: bool,
    item_id: int,
    name: str,
    description: str,
    category: int,
    images_qty: int
):  
    data = {
        "seller_id":          seller_id,
        "is_verified_seller": is_verified_seller,
        "item_id":            item_id,
        "name":               name,
        "description":        description,
        "category":           category,
        "images_qty":         images_qty
    }
    
    response = app_client.post('/predict', json=data)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

# seller_id должен быть int, а не str
@pytest.mark.parametrize('seller_id', ['str'])
@pytest.mark.parametrize('is_verified_seller', [False])
@pytest.mark.parametrize('item_id', [1])
@pytest.mark.parametrize('name', ['test'])
@pytest.mark.parametrize('description', ['description'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [0])
def test_seller_id_string_type(
    app_client: TestClient,
    seller_id: str,
    is_verified_seller: bool,
    item_id: int,
    name: str,
    description: str,
    category: int,
    images_qty: int
):
    data = {
        "seller_id":          seller_id,
        "is_verified_seller": is_verified_seller,
        "item_id":            item_id,
        "name":               name,
        "description":        description,
        "category":           category,
        "images_qty":         images_qty
    }
    
    response = app_client.post('/predict', json=data)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

# is_verified_seller должен быть bool, а не str
@pytest.mark.parametrize('seller_id', [1])
@pytest.mark.parametrize('is_verified_seller', ['str'])
@pytest.mark.parametrize('item_id', [1])
@pytest.mark.parametrize('name', ['test'])
@pytest.mark.parametrize('description', ['description'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [0])
def test_is_verified_seller_string_type(
    app_client: TestClient,
    seller_id: int,
    is_verified_seller: str,
    item_id: int,
    name: str,
    description: str,
    category: int,
    images_qty: int
):
    data = {
        "seller_id":          seller_id,
        "is_verified_seller": is_verified_seller,
        "item_id":            item_id,
        "name":               name,
        "description":        description,
        "category":           category,
        "images_qty":         images_qty
    }
    
    response = app_client.post('/predict', json=data)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

# item_id должен быть int, а не str
@pytest.mark.parametrize('seller_id', [1])
@pytest.mark.parametrize('is_verified_seller', [False])
@pytest.mark.parametrize('item_id', ['str'])
@pytest.mark.parametrize('name', ['test'])
@pytest.mark.parametrize('description', ['description'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [0])
def test_item_id_string_type(
    app_client: TestClient,
    seller_id: int,
    is_verified_seller: bool,
    item_id: str,
    name: str,
    description: str,
    category: int,
    images_qty: int
):
    data = {
        "seller_id":          seller_id,
        "is_verified_seller": is_verified_seller,
        "item_id":            item_id,
        "name":               name,
        "description":        description,
        "category":           category,
        "images_qty":         images_qty
    }
    
    response = app_client.post('/predict', json=data)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

# name должен быть str, а не int
@pytest.mark.parametrize('seller_id', [1])
@pytest.mark.parametrize('is_verified_seller', [False])
@pytest.mark.parametrize('item_id', [1])
@pytest.mark.parametrize('name', [123]) 
@pytest.mark.parametrize('description', ['description'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [0])
def test_name_int_type(
    app_client: TestClient,
    seller_id: int,
    is_verified_seller: bool,
    item_id: int,
    name: int,
    description: str,
    category: int,
    images_qty: int
):
    data = {
        "seller_id":          seller_id,
        "is_verified_seller": is_verified_seller,
        "item_id":            item_id,
        "name":               name,
        "description":        description,
        "category":           category,
        "images_qty":         images_qty
    }
    
    response = app_client.post('/predict', json=data)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

# description должен быть str, а не int
@pytest.mark.parametrize('seller_id', [1])
@pytest.mark.parametrize('is_verified_seller', [False])
@pytest.mark.parametrize('item_id', [1])
@pytest.mark.parametrize('name', ['test'])
@pytest.mark.parametrize('description', [123])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [0])
def test_description_int_type(
    app_client: TestClient,
    seller_id: int,
    is_verified_seller: bool,
    item_id: int,
    name: str,
    description: int,
    category: int,
    images_qty: int
):
    data = {
        "seller_id":          seller_id,
        "is_verified_seller": is_verified_seller,
        "item_id":            item_id,
        "name":               name,
        "description":        description,
        "category":           category,
        "images_qty":         images_qty
    }
    
    response = app_client.post('/predict', json=data)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

# category должен быть int, а не str
@pytest.mark.parametrize('seller_id', [1])
@pytest.mark.parametrize('is_verified_seller', [False])
@pytest.mark.parametrize('item_id', [1])
@pytest.mark.parametrize('name', ['test'])
@pytest.mark.parametrize('description', ['description'])
@pytest.mark.parametrize('category', ['str'])
@pytest.mark.parametrize('images_qty', [0])
def test_category_string_type(
    app_client: TestClient,
    seller_id: int,
    is_verified_seller: bool,
    item_id: int,
    name: str,
    description: str,
    category: str,
    images_qty: int
):
    data = {
        "seller_id":          seller_id,
        "is_verified_seller": is_verified_seller,
        "item_id":            item_id,
        "name":               name,
        "description":        description,
        "category":           category,
        "images_qty":         images_qty
    }
    
    response = app_client.post('/predict', json=data)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

# images_qty должен быть int, а не str
@pytest.mark.parametrize('seller_id', [1])
@pytest.mark.parametrize('is_verified_seller', [False])
@pytest.mark.parametrize('item_id', [1])
@pytest.mark.parametrize('name', ['test'])
@pytest.mark.parametrize('description', ['description'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', ['str'])
def test_images_qty_string_type(
    app_client: TestClient,
    seller_id: int,
    is_verified_seller: bool,
    item_id: int,
    name: str,
    description: str,
    category: int,
    images_qty: str
):
    data = {
        "seller_id":          seller_id,
        "is_verified_seller": is_verified_seller,
        "item_id":            item_id,
        "name":               name,
        "description":        description,
        "category":           category,
        "images_qty":         images_qty
    }
    
    response = app_client.post('/predict', json=data)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
