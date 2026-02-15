import pytest
import asyncio
from main import app
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from schemas.async_prediction import AsyncPredictRequest
from services.async_prediction_service import async_predict as async_prediction_service
from services.moderation_result_service import get_moderation_result
from repositories.users import UserPostgresStorage
from repositories.advertisements import AdvertisementPostgresStorage
from repositories.moderations import ModerationResultRepository
from fastapi.testclient import TestClient
from http import HTTPStatus

from errors import AdvertisementNotFoundError, UserNotFoundError, AdvertisementCreationError, UserNotCreationError

IDS = [1, 100, 1000, 1_000_000]

@pytest.fixture
def app_client():
    with TestClient(app) as client:
        yield client

### ---------------------- ТЕСТЫ ТАБЛИЦЫ USERS ------------------------------------------
@pytest.mark.integration
@pytest.mark.parametrize('seller_id', IDS)
@pytest.mark.parametrize('is_verified_seller', [True])
async def test_create_and_remove_users(seller_id, is_verified_seller):    
    expected_row = {
        'seller_id': seller_id,
        'is_verified_seller': is_verified_seller,
    }
    
    storage = UserPostgresStorage()
    
    result = await storage.create(seller_id, is_verified_seller)

    assert result == expected_row

    remove_result = await storage.delete(seller_id)

    assert remove_result == expected_row

async def test_create_user_exist():    
    seller_id = 1
    is_verified_seller = True

    storage = UserPostgresStorage()
    await storage.create(seller_id, is_verified_seller)

    with pytest.raises(UserNotCreationError)  as exc_info:
        await storage.create(seller_id, is_verified_seller)
    
    await storage.delete(seller_id)

@pytest.mark.integration
@pytest.mark.parametrize('seller_id', IDS)
@pytest.mark.parametrize('is_verified_seller', [True])
async def test_select_users(seller_id, is_verified_seller): 

    expected_row = {
        'seller_id': seller_id,
        'is_verified_seller': is_verified_seller,
    }

    storage = UserPostgresStorage()

    await storage.create(**expected_row)

    result = await storage.select(seller_id)
    
    assert result == expected_row

    await storage.delete(seller_id)

async def test_select_and_delete_user_not_found():    
    seller_id = 2

    storage = UserPostgresStorage()
    
    with pytest.raises(UserNotFoundError):
        await storage.select(seller_id)

    with pytest.raises(UserNotFoundError):
        await storage.delete(seller_id)


### ---------------------- ТЕСТЫ ТАБЛИЦЫ ADVERTISEMENTS ------------------------------------------
@pytest.mark.integration
@pytest.mark.parametrize('item_id,seller_id', zip(IDS, IDS))
@pytest.mark.parametrize('name', ['Test name'])
@pytest.mark.parametrize('description', ['Test desc'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [5])
async def test_create_and_remove_advertisements(item_id, seller_id, name, description, category, images_qty):    
    expected_row = {
        'item_id': item_id,
        'seller_id': seller_id,
        'name': name,
        'description': description,
        'category': category,
        'images_qty': images_qty,
        'is_closed': False
    }

    user_storage = UserPostgresStorage()
    
    await user_storage.create(seller_id, True)
    
    adv_storage = AdvertisementPostgresStorage()
    
    result = await adv_storage.create(**expected_row)

    assert result == expected_row

    remove_result = await adv_storage.delete(item_id)

    assert remove_result == expected_row

    await user_storage.delete(seller_id)

@pytest.mark.integration
async def test_create_advertisement_exist():
    seller_id = 1
    item_id = 1

    expected_row = {
        'item_id': item_id,
        'seller_id': seller_id,
        'name': 'Test name',
        'description': 'Test desc',
        'category': 1,
        'images_qty': 5,
        'is_closed': False
    } 

    user_storage = UserPostgresStorage()
    
    await user_storage.create(seller_id, True)
    
    adv_storage = AdvertisementPostgresStorage()
    await adv_storage.create(**expected_row)

    with pytest.raises(AdvertisementCreationError) as exc_info:
        await adv_storage.create(**expected_row)

    await adv_storage.delete(item_id)
    await user_storage.delete(seller_id)

@pytest.mark.integration
@pytest.mark.parametrize('item_id,seller_id', zip(IDS, IDS))
@pytest.mark.parametrize('name', ['Test name'])
@pytest.mark.parametrize('description', ['Test desc'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [5])
async def test_select_advertisements(item_id, seller_id, name, description, category, images_qty): 

    expected_row = {
        'item_id': item_id,
        'seller_id': seller_id,
        'name': name,
        'description': description,
        'category': category,
        'images_qty': images_qty,
        'is_closed': False
    }

    user_storage = UserPostgresStorage()
    adv_storage = AdvertisementPostgresStorage()

    await user_storage.create(seller_id, True)
    await adv_storage.create(**expected_row)

    result = await adv_storage.select(item_id)
    
    assert result == expected_row

    await adv_storage.delete(item_id)
    await user_storage.delete(seller_id)

@pytest.mark.integration
async def test_select_and_delete_advertisement_not_found():    
    item_id = 2

    storage = AdvertisementPostgresStorage()
    
    with pytest.raises(AdvertisementNotFoundError):
        await storage.select(item_id)

    with pytest.raises(AdvertisementNotFoundError):
        await storage.delete(item_id)

### ---------------------- ТЕСТЫ МОДЕРАЦИИ ------------------------------------------

@pytest.fixture
def mock_advertisement_repo():
    with patch('services.async_prediction_service.AdvertisementRepository') as mock_repo:
        mock_instance = AsyncMock()
        mock_instance.exists.return_value = True
        mock_repo.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_kafka_producer():
    mock = AsyncMock()
    mock.send_moderation_request = AsyncMock()
    return mock

@pytest.mark.parametrize('item_id', IDS)
@pytest.mark.integration
async def test_create_and_remove_moderation_task(item_id, mock_kafka_producer): 
    seller_id = 1

    adv_data = {
        'item_id': item_id,
        'seller_id': seller_id,
        'name': 'Test name',
        'description': 'Test desc',
        'category': 1,
        'images_qty': 5,
        'is_closed': False
    } 

    user_storage = UserPostgresStorage()
    adv_storage = AdvertisementPostgresStorage()

    await user_storage.create(seller_id, True)
    await adv_storage.create(**adv_data)

    mod_rep = ModerationResultRepository()   
    await mod_rep.truncate()

    request = AsyncPredictRequest(item_id=item_id)
    
    response = await async_prediction_service(request, mock_kafka_producer)
    
    assert response.task_id == 1
    assert response.status == "pending"
    assert response.message == "Moderation request accepted"

    remove_result = await mod_rep.delete(response.task_id)

    assert remove_result.id == 1
    assert remove_result.item_id == item_id
    assert remove_result.status == "pending"

    await adv_storage.delete(item_id)
    await user_storage.delete(seller_id)


@pytest.mark.parametrize('item_id', IDS)
@pytest.mark.integration
async def test_create_moderation_with_no_advertisement(item_id, mock_kafka_producer):
    request = AsyncPredictRequest(item_id=item_id)
    
    with pytest.raises(AdvertisementNotFoundError) as exc_info:
        await async_prediction_service(request, mock_kafka_producer)
    
    assert "не найдено" in str(exc_info.value)

@pytest.mark.parametrize('item_id', IDS)
async def test_get_moderation_result(item_id, mock_kafka_producer):
    seller_id = 1

    adv_data = {
        'item_id': item_id,
        'seller_id': seller_id,
        'name': 'Test name',
        'description': 'Test desc',
        'category': 1,
        'images_qty': 5,
        'is_closed': False
    } 

    user_storage = UserPostgresStorage()
    adv_storage = AdvertisementPostgresStorage()

    await user_storage.create(seller_id, True)
    await adv_storage.create(**adv_data)

    mod_rep = ModerationResultRepository()   
    await mod_rep.truncate()

    request = AsyncPredictRequest(item_id=item_id)
    
    response = await async_prediction_service(request, mock_kafka_producer) 

    result = await get_moderation_result(task_id=1)
    
    assert result.id == 1
    assert result.item_id == item_id
    assert result.status == "pending"

    await mod_rep.delete(response.task_id)

    await adv_storage.delete(item_id)
    await user_storage.delete(seller_id)

@pytest.mark.parametrize('task_id', [id * 2 for id in IDS])
@pytest.mark.integration
async def test_get_moderation_result_not_found(task_id):    
    with pytest.raises(Exception) as exc_info:
        await get_moderation_result(task_id)
    
    assert "не найдена" in str(exc_info.value)

### ---------------------- ТЕСТЫ НА УДАЛЕНИЕ ------------------------------------------
@pytest.mark.integration
@pytest.mark.parametrize('item_id,seller_id', zip(IDS, IDS))
@pytest.mark.parametrize('name', ['Test name'])
@pytest.mark.parametrize('description', ['Test desc'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [5])
async def test_close_advertisements(app_client, item_id, seller_id, name, description, category, images_qty):    
    adv_data = {
        'item_id': item_id,
        'seller_id': seller_id,
        'name': name,
        'description': description,
        'category': category,
        'images_qty': images_qty,
        'is_closed': False
    }

    data = {
        'item_id': item_id
    }

    user_storage = UserPostgresStorage()
    
    await user_storage.create(seller_id, True)
    
    adv_storage = AdvertisementPostgresStorage()
    
    result = await adv_storage.create(**adv_data)
    
    response = app_client.post(f'/close/{item_id}', json=data)
    response_data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert response_data == adv_data

    await user_storage.delete(seller_id)
