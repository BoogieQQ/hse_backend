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