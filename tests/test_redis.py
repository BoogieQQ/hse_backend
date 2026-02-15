import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import timedelta
from json import dumps, loads
from unittest import mock

from fastapi.testclient import TestClient
from main import app
from repositories.advertisements import AdvertisementRepository, AdvertisementPostgresStorage, AdvertisementRedisStorage
from repositories.users import UserRepository

from errors import AdvertisementNotFoundError
from schemas.prediction import PredictionResponse

@pytest.fixture
def mock_redis():
    with patch('repositories.advertisements.get_redis_connection') as mock_get_redis:
        mock_redis_conn = AsyncMock()
        mock_redis_conn.get = AsyncMock(return_value=None)
        mock_redis_conn.set = AsyncMock()
        mock_redis_conn.delete = AsyncMock()
        mock_redis_conn.pipeline = MagicMock()
        
        mock_pipeline = AsyncMock()
        mock_pipeline.set = MagicMock()
        mock_pipeline.expire = MagicMock()
        mock_pipeline.execute = AsyncMock()
        mock_redis_conn.pipeline.return_value = mock_pipeline
        
        mock_get_redis.return_value.__aenter__.return_value = mock_redis_conn
        
        yield {
            'get_redis': mock_get_redis,
            'redis_conn': mock_redis_conn,
            'pipeline': mock_pipeline
        }

# ----------------------------- ЮНИТ-ТЕСТЫ ------------------------------------
@pytest.mark.asyncio
async def test_check_cache_hit():
    mock_redis_storage = AsyncMock(spec=AdvertisementRedisStorage)
    mock_redis_storage.get.return_value = {'is_violation': True, 'probability': 0.95}
    
    mock_postgres_storage = AsyncMock(spec=AdvertisementPostgresStorage)
    
    repo = AdvertisementRepository(
        advertisement_redis_storage=mock_redis_storage,
        advertisement_postgres_storage=mock_postgres_storage
    )
    
    item_id = 1
    result = await repo.check_cache(item_id)
    
    assert isinstance(result, PredictionResponse)
    assert result.is_violation == True
    assert result.probability == 0.95
    mock_redis_storage.get.assert_called_once_with(item_id)


@pytest.mark.asyncio
async def test_check_cache_miss():
    mock_redis_storage = AsyncMock(spec=AdvertisementRedisStorage)
    mock_redis_storage.get.return_value = None
    
    mock_postgres_storage = AsyncMock(spec=AdvertisementPostgresStorage)
    
    repo = AdvertisementRepository(
        advertisement_redis_storage=mock_redis_storage,
        advertisement_postgres_storage=mock_postgres_storage
    )
    
    item_id = 1
    result = await repo.check_cache(item_id)
    
    assert result is None
    mock_redis_storage.get.assert_called_once_with(item_id)


@pytest.mark.asyncio
async def test_to_cache_correct_args():
    mock_redis_storage = AsyncMock(spec=AdvertisementRedisStorage)
    
    mock_postgres_storage = AsyncMock(spec=AdvertisementPostgresStorage)
    
    repo = AdvertisementRepository(
        advertisement_redis_storage=mock_redis_storage,
        advertisement_postgres_storage=mock_postgres_storage
    )
    
    item_id = 1
    is_violation = True
    probability = 0.95
    
    await repo.to_cache(item_id, is_violation, probability)
    
    mock_redis_storage.set.assert_called_once_with(
        item_id, 
        row={'is_violation': is_violation, 'probability': probability}
    )

# ---------------------------- ИНТЕГРАЦИОННЫЕ ТЕСТЫ --------------------------------
@pytest.mark.asyncio
@pytest.mark.integration
async def test_redis_set_get():

    redis_storage = AdvertisementRedisStorage(_TTL=timedelta(seconds=10))
    
    item_id = 123
    test_data = {'is_violation': True, 'probability': 0.95, 'text': 'test'}
    
    await redis_storage.set(item_id, test_data)
    
    result = await redis_storage.get(item_id)
    
    assert result == test_data
    assert isinstance(result, dict)
    assert result['is_violation'] is True
    assert result['probability'] == 0.95

@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_storage_get_nonexistent():
    redis_storage = AdvertisementRedisStorage()
    
    result = await redis_storage.get(999999)
    
    assert result is None

@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_delete():
    redis_storage = AdvertisementRedisStorage(_TTL=timedelta(seconds=10))
    
    item_id = 456
    test_data = {'is_violation': False, 'probability': 0.10}
    
    await redis_storage.set(item_id, test_data)
    
    result_before = await redis_storage.get(item_id)
    assert result_before == test_data
    
    await redis_storage.delete(item_id)
    
    result_after = await redis_storage.get(item_id)
    assert result_after is None

@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_delete_advertisement():
    item_id = 1
    seller_id = 1

    user_data = {
        'seller_id': seller_id,
        'is_verified_seller': True,
    }
    
    user_storage = UserRepository()
    
    _ = await user_storage.create(**user_data)

    adv_row = {
        'item_id': item_id,
        'seller_id': seller_id,
        'name': 'test',
        'description': 'test',
        'category': 1,
        'images_qty': 10,
        'is_closed': False
    }
    
    adv_storage = AdvertisementRepository()
    
    _ = await adv_storage.create(**adv_row)

    redis_storage = AdvertisementRedisStorage(_TTL=timedelta(seconds=30))
    
    test_data = {'is_violation': False, 'probability': 0.10}
    
    await redis_storage.set(item_id, test_data)
    
    result_before = await redis_storage.get(item_id)
    assert result_before == test_data

    await adv_storage.delete(item_id)
    await user_storage.delete(seller_id)

    result_after = await redis_storage.get(item_id)
    assert result_after is None
