import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from schemas.async_prediction import AsyncPredictRequest
from services.async_prediction_service import async_predict as async_prediction_service
from services.moderation_result_service import get_moderation_result
from errors import AdvertisementNotFoundError, UserNotFoundError
from repositories.users import UserPostgresStorage
from repositories.advertisements import AdvertisementPostgresStorage
from repositories.moderations import ModerationResultRepository

from errors import AdvertisementNotFoundError, UserNotFoundError, AdvertisementCreationError, UserNotCreationError

IDS = [1, 100, 1000, 1_000_000]

### ---------------------- ТЕСТЫ ТАБЛИЦЫ USERS ------------------------------------------
@pytest.mark.parametrize('seller_id', IDS)
@pytest.mark.parametrize('is_verified_seller', [True])
async def test_create_users(seller_id, is_verified_seller):    
    expected_row = {
        'seller_id': seller_id,
        'is_verified_seller': is_verified_seller,
    }
    
    storage = UserPostgresStorage()
    
    result = await storage.create(seller_id, is_verified_seller)

    assert result == expected_row

async def test_create_user_exist():    
    seller_id = 1
    is_verified_seller = True

    storage = UserPostgresStorage()
    
    with pytest.raises(UserNotCreationError)  as exc_info:
        await storage.create(seller_id, is_verified_seller)

@pytest.mark.parametrize('seller_id', IDS)
@pytest.mark.parametrize('is_verified_seller', [True])
async def test_select_users(seller_id, is_verified_seller): 

    expected_row = {
        'seller_id': seller_id,
        'is_verified_seller': is_verified_seller,
    }

    storage = UserPostgresStorage()

    result = await storage.select(seller_id)
    
    assert result == expected_row

async def test_select_and_delete_user_not_found():    
    seller_id = 2

    storage = UserPostgresStorage()
    
    with pytest.raises(UserNotFoundError):
        await storage.select(seller_id)

    with pytest.raises(UserNotFoundError):
        await storage.delete(seller_id)


### ---------------------- ТЕСТЫ ТАБЛИЦЫ ADVERTISEMENTS ------------------------------------------
@pytest.mark.parametrize('item_id,seller_id', zip(IDS, IDS))
@pytest.mark.parametrize('name', ['Test name'])
@pytest.mark.parametrize('description', ['Test desc'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [5])
async def test_create_advertisements(item_id, seller_id, name, description, category, images_qty):    
    expected_row = {
        'item_id': item_id,
        'seller_id': seller_id,
        'name': name,
        'description': description,
        'category': category,
        'images_qty': images_qty,
    }
    
    storage = AdvertisementPostgresStorage()
    
    result = await storage.create(item_id, seller_id, name, description, category, images_qty)

    assert result == expected_row

async def test_create_advertisement_exist():    
    item_id = 1
    seller_id = 1
    name = 'Test name'
    description = 'Test desc'
    category = 1
    images_qty = 5

    storage = AdvertisementPostgresStorage()
    
    with pytest.raises(AdvertisementCreationError) as exc_info:
        await storage.create(item_id, seller_id, name, description, category, images_qty)

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
    }

    storage = AdvertisementPostgresStorage()

    result = await storage.select(item_id)
    
    assert result == expected_row

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
async def test_create_moderation_task(item_id, mock_kafka_producer): 

    mod_rep = ModerationResultRepository()   
    await mod_rep.truncate()

    request = AsyncPredictRequest(item_id=item_id)
    
    response = await async_prediction_service(request, mock_kafka_producer)
    
    assert response.task_id == 1
    assert response.status == "pending"
    assert response.message == "Moderation request accepted"


@pytest.mark.parametrize('item_id', IDS)
async def test_create_moderation_with_no_advertisement(item_id, mock_advertisement_repo, mock_kafka_producer):
    mock_advertisement_repo.exists.return_value = False

    request = AsyncPredictRequest(item_id=item_id)
    
    with pytest.raises(Exception) as exc_info:
        await async_prediction_service(request, mock_kafka_producer)
    
    assert "не найдено" in str(exc_info.value)

@pytest.mark.parametrize('item_id', IDS)
async def test_get_moderation_result(item_id, mock_kafka_producer):
    mod_rep = ModerationResultRepository()   
    await mod_rep.truncate()

    request = AsyncPredictRequest(item_id=item_id)
    
    response = await async_prediction_service(request, mock_kafka_producer) 

    result = await get_moderation_result(task_id=1)
    
    assert result.id == 1
    assert result.item_id == item_id
    assert result.status == "pending"

@pytest.mark.parametrize('task_id', [id * 2 for id in IDS])
async def test_get_moderation_result_not_found(task_id):    
    with pytest.raises(Exception) as exc_info:
        await get_moderation_result(task_id)
    
    assert "не найдена" in str(exc_info.value)

### ---------------------- ТЕСТ ЛОГИКИ ВОРКЕРА ------------------------------------------
@pytest.fixture
def mock_moderation_repo_worker():
    with patch('repositories.moderations.ModerationResultRepository') as mock_repo:
        mock_instance = AsyncMock()
        mock_instance.get.return_value = MagicMock(item_id=1)
        mock_instance.update = AsyncMock()
        mock_repo.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_advertisement_repo_worker():
    with patch('repositories.advertisements.AdvertisementRepository') as mock_repo:
        mock_instance = AsyncMock()
        mock_instance.exists.return_value = True
        mock_instance.get.return_value = MagicMock(
            item_id=1,
            seller_id=1,
            name="Test",
            description="Test desc",
            category=1,
            images_qty=5
        )
        mock_repo.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_user_repo_worker():
    with patch('repositories.users.UserRepository') as mock_repo:
        mock_instance = AsyncMock()
        mock_instance.get.return_value = MagicMock(
            seller_id=1,
            is_verified_seller=True
        )
        mock_repo.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_model_service_worker():
    with patch('services.model_service.ModelService') as mock_service:
        mock_instance = Mock()
        mock_instance.extract_features.return_value = [1.0, 2.0, 3.0]
        mock_instance.predict.return_value = (False, 0.1)
        mock_service.extract_features = mock_instance.extract_features
        mock_service.predict = mock_instance.predict
        yield mock_instance


@pytest.mark.parametrize('task_id', [1, 2])
async def test_worker_message_processing(task_id, mock_moderation_repo_worker, mock_advertisement_repo_worker, 
                                        mock_user_repo_worker, mock_model_service_worker):    
    message_data = {'item_id': task_id}
    message_bytes = str(message_data).encode('utf-8')
    
    mock_msg = Mock()
    mock_msg.value = message_bytes
    
    message = mock_msg.value.decode('utf-8')
    parsed_message = eval(message)
    received_task_id = parsed_message['item_id']
    
    moderation_task = await mock_moderation_repo_worker.get(received_task_id)
    item_id = moderation_task.item_id
    
    exists = await mock_advertisement_repo_worker.exists(item_id)
    assert exists == True
    
    advertisement = await mock_advertisement_repo_worker.get(item_id)
    user = await mock_user_repo_worker.get(advertisement.seller_id)
    
    ad_data = {"item_id": advertisement.item_id, "seller_id": advertisement.seller_id}
    user_data = {"seller_id": user.seller_id, "is_verified_seller": user.is_verified_seller}
    request = {**ad_data, **user_data}
    
    features = mock_model_service_worker.extract_features(request)
    is_violation, probability = mock_model_service_worker.predict(features)
    
    await mock_moderation_repo_worker.update(
        task_id=received_task_id,
        status='completed',
        is_violation=is_violation,
        probability=probability
    )
    
    mock_moderation_repo_worker.get.assert_called_once_with(received_task_id)
    mock_advertisement_repo_worker.exists.assert_called_once_with(item_id)
    mock_advertisement_repo_worker.get.assert_called_once_with(item_id)
    mock_user_repo_worker.get.assert_called_once_with(advertisement.seller_id)
    mock_moderation_repo_worker.update.assert_called_once_with(
        task_id=received_task_id,
        status='completed',
        is_violation=False,
        probability=0.1
    )

### ---------------------- ТЕСТ ОТПРАВКИ В DLQ ------------------------------------------

@pytest.fixture
def mock_moderation_repo_dlq():
    with patch('repositories.moderations.ModerationResultRepository') as mock_repo:
        mock_instance = AsyncMock()
        mock_instance.get.side_effect = Exception("Test error")
        mock_instance.update_failed = AsyncMock()
        mock_repo.return_value = mock_instance
        yield mock_instance

@pytest.mark.parametrize('retry_count', [3, 5])
async def test_send_to_dlq_on_error(retry_count, mock_moderation_repo_dlq):    
    message_data = {'item_id': 1}
    message_bytes = str(message_data).encode('utf-8')
    
    mock_msg = Mock()
    mock_msg.value = message_bytes
    
    mock_producer = AsyncMock()
    mock_producer.send_and_wait = AsyncMock()
    
    for retry in range(1, retry_count + 1):
        try:
            message = mock_msg.value.decode('utf-8')
            parsed_message = eval(message)
            task_id = parsed_message['item_id']
            
            await mock_moderation_repo_dlq.get(task_id)
            
        except Exception as e:
            if retry == retry_count:
                dlq_message = {
                    'item_id': task_id,
                    'error': f'All retries failed: {e}',
                    'original_message': message
                }
                
                await mock_producer.send_and_wait(
                    'dlq_topic',
                    str(dlq_message).encode('utf-8')
                )
                
                await mock_moderation_repo_dlq.update_failed(
                    task_id=task_id,
                    status='failed',
                    error_message=str(e)
                )
                
                mock_producer.send_and_wait.assert_called_once()
                mock_moderation_repo_dlq.update_failed.assert_called_once_with(
                    task_id=task_id,
                    status='failed',
                    error_message="Test error"
                )
                break

### ---------------------- ТЕСТЫ НА УДАЛЕНИЕ ------------------------------------------
@pytest.mark.parametrize('item_id,seller_id', zip(IDS, IDS))
@pytest.mark.parametrize('name', ['Test name'])
@pytest.mark.parametrize('description', ['Test desc'])
@pytest.mark.parametrize('category', [1])
@pytest.mark.parametrize('images_qty', [5])
async def test_delete_advertisements(item_id, seller_id, name, description, category, images_qty):    
    expected_row = {
        'item_id': item_id,
        'seller_id': seller_id,
        'name': name,
        'description': description,
        'category': category,
        'images_qty': images_qty,
    }
    
    storage = AdvertisementPostgresStorage()
    
    result = await storage.delete(item_id)
    assert result == expected_row


@pytest.mark.parametrize('seller_id', IDS)
@pytest.mark.parametrize('is_verified_seller', [True])
async def test_delete_users(seller_id, is_verified_seller):    
    expected_row = {
        'seller_id': seller_id,
        'is_verified_seller': is_verified_seller
    }
    
    storage = UserPostgresStorage()
    
    result = await storage.delete(seller_id)
    assert result == expected_row