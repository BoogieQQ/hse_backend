import pytest

from fastapi.testclient import TestClient
from main import app
from http import HTTPStatus


@pytest.fixture
def app_client():
    with TestClient(app) as client:
        yield client


### ---------------------- ТЕСТЫ НА РАБОТУ МЛ-МОДЕЛИ ------------------------------------------

@pytest.mark.parametrize(
    "test_name,is_verified,images_qty,description,category",
    [
    ("verified_seller_few_images", True, 2, "desc", 10),
    ("unverified_seller_no_images", False, 0, "desc" * 4, 5),
    ("verified_seller_many_images", True, 8, "desc" * 20, 25),
    ("unverified_seller_many_images", False, 10, "desc" * 3, 15),
    ("verified_seller_max_images", True, 10, "desc" * 8, 1),
    ("unverified_minimal_data", False, 0, "", 1),
    ]
)
def test_predict_success_cases(
    app_client,
    test_name,
    is_verified,
    images_qty,
    description,
    category
):    
    data = {
        "seller_id": 1,
        "is_verified_seller": is_verified,
        "item_id": 1,
        "name": f"Test Item",
        "description": description,
        "category": category,
        "images_qty": images_qty
    }

    is_violation = (data['is_verified_seller'] == False) & (data['images_qty'] < 2)
    
    response = app_client.post('/predict', json=data)
    
    assert response.status_code == HTTPStatus.OK
    response_data = response.json()
    assert response_data["is_violation"] == is_violation
    assert 0.0 <= response_data["probability"] <= 1.0

### ---------------------- ТЕСТЫ ВАЛИДАЦИИ ВХОДНЫХ ЗНАЧЕНИЙ ------------------------------------------

# Тест на seller_id > 0
@pytest.mark.parametrize('seller_id', [0, -5, -10, -1000, -1000000])
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
@pytest.mark.parametrize('item_id', [0, -5, -10, -1000, -1000000])
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
@pytest.mark.parametrize('name', ['*' * 257, '*' * 258, '*' * 300, '*' * 1000, '*' * 1_000_000])
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
@pytest.mark.parametrize('description', ['a' * (2**14 + 1), 'a' * (2**14 + 2), 'a' * (2**15), 'a' * 1_000_000])
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
@pytest.mark.parametrize('images_qty', [-1, -3, -5, -10, -1000, -1_000_000])
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

### ---------------------- ТЕСТЫ ВАЛИДАЦИИ ВХОДНЫХ ТИПОВ ------------------------------------------

# seller_id должен быть int, а не что-то другое
@pytest.mark.parametrize('seller_id', ['str', False, 1.1])
@pytest.mark.parametrize('is_verified_seller', [False])
@pytest.mark.parametrize('item_id', [1])
@pytest.mark.parametrize('name', ['test'])
@pytest.mark.parametrize('description', ['description'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [0])
def test_seller_id_int_type(
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

# is_verified_seller должен быть bool, а не что-то другое
@pytest.mark.parametrize('seller_id', [1])
@pytest.mark.parametrize('is_verified_seller', ['str', 3, 1.1])
@pytest.mark.parametrize('item_id', [1])
@pytest.mark.parametrize('name', ['test'])
@pytest.mark.parametrize('description', ['description'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [0])
def test_is_verified_seller_bool_type(
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

# item_id должен быть int, а не что-то другое
@pytest.mark.parametrize('seller_id', [1])
@pytest.mark.parametrize('is_verified_seller', [False])
@pytest.mark.parametrize('item_id', ['str', False, 1.1])
@pytest.mark.parametrize('name', ['test'])
@pytest.mark.parametrize('description', ['description'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [0])
def test_item_id_int_type(
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

# name должен быть str, а не что-то другое
@pytest.mark.parametrize('seller_id', [1])
@pytest.mark.parametrize('is_verified_seller', [False])
@pytest.mark.parametrize('item_id', [1])
@pytest.mark.parametrize('name', [1, False, 1.1]) 
@pytest.mark.parametrize('description', ['description'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [0])
def test_name_str_type(
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

# description должен быть str, а не что-то другое
@pytest.mark.parametrize('seller_id', [1])
@pytest.mark.parametrize('is_verified_seller', [False])
@pytest.mark.parametrize('item_id', [1])
@pytest.mark.parametrize('name', ['test'])
@pytest.mark.parametrize('description', [1, False, 1.1])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [0])
def test_description_str_type(
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

# category должен быть int, а не что-то другое
@pytest.mark.parametrize('seller_id', [1])
@pytest.mark.parametrize('is_verified_seller', [False])
@pytest.mark.parametrize('item_id', [1])
@pytest.mark.parametrize('name', ['test'])
@pytest.mark.parametrize('description', ['description'])
@pytest.mark.parametrize('category', ['str', False, 1.1])
@pytest.mark.parametrize('images_qty', [0])
def test_category_int_type(
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
@pytest.mark.parametrize('images_qty', ['str', 1.1])
def test_images_qty_int_type(
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
