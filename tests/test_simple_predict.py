import pytest

from fastapi.testclient import TestClient
from main import app
from http import HTTPStatus
from fastapi import HTTPException
from unittest.mock import patch, AsyncMock, MagicMock
from schemas.prediction import PredictionResponse

from repositories.users import UserRepository
from repositories.advertisements import AdvertisementRepository
from repositories.users import UserRepository
from errors import AdvertisementNotFoundError, UserNotFoundError, AdvertisementCreationError

@pytest.fixture
def app_client():
    with TestClient(app) as client:
        yield client


@pytest.mark.parametrize(
    "test_name,is_verified,images_qty,description,category,expected_violation",
    [
        ("verified_seller_few_images", True, 2, "desc", 10, False),
        ("unverified_seller_no_images", False, 0, "desc" * 4, 5, True),
        ("verified_seller_many_images", True, 8, "desc" * 20, 25, False),
        ("unverified_seller_many_images", False, 10, "desc" * 3, 15, False),
        ("verified_seller_max_images", True, 10, "desc" * 8, 1, False),
        ("unverified_minimal_data", False, 0, "", 1, True),
    ]
)
def test_simple_predict_success_cases(
    app_client,
    test_name,
    is_verified,
    images_qty,
    description,
    category,
    expected_violation
):
    item_id = 1
    seller_id = 1
    
    with patch('services.simple_prediction_service.AdvertisementRepository') as MockAdRepo, \
         patch('services.simple_prediction_service.UserRepository') as MockUserRepo:
        
        mock_ad_repo_instance = AsyncMock()
        mock_user_repo_instance = AsyncMock()
        
        MockAdRepo.return_value = mock_ad_repo_instance
        MockUserRepo.return_value = mock_user_repo_instance
        
        mock_ad = MagicMock()
        mock_ad.item_id = item_id
        mock_ad.seller_id = seller_id
        mock_ad.name = test_name
        mock_ad.description = description
        mock_ad.category = category
        mock_ad.images_qty = images_qty
        mock_ad.model_dump = MagicMock(return_value={
            'item_id': item_id,
            'seller_id': seller_id,
            'name': test_name,
            'description': description,
            'category': category,
            'images_qty': images_qty
        })
        
        mock_user = MagicMock()
        mock_user.seller_id = seller_id
        mock_user.is_verified_seller = is_verified
        mock_user.model_dump = MagicMock(return_value={
            'seller_id': seller_id,
            'is_verified_seller': is_verified
        })
        
        mock_ad_repo_instance.check_cache = AsyncMock(return_value=None)
        mock_ad_repo_instance.to_cache = AsyncMock()

        mock_ad_repo_instance.get = AsyncMock(return_value=mock_ad)
        mock_user_repo_instance.get = AsyncMock(return_value=mock_user)
        
        response = app_client.post('/simple_predict', json={'item_id': item_id})
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["is_violation"] == expected_violation
        assert 0.0 <= response_data["probability"] <= 1.0
        
        mock_ad_repo_instance.check_cache.assert_called_once_with(item_id)
        mock_ad_repo_instance.get.assert_called_once_with(item_id)
        mock_user_repo_instance.get.assert_called_once_with(seller_id)
        mock_ad_repo_instance.to_cache.assert_called_once()

async def test_simple_predict_with_cached_result(
    app_client
):

    item_id = 1
    with patch('services.simple_prediction_service.AdvertisementRepository') as MockAdRepo:

        mock_ad_repo_instance = AsyncMock()
        MockAdRepo.return_value = mock_ad_repo_instance

        cached_result = PredictionResponse(is_violation=True, probability=0.95)

        mock_ad_repo_instance.check_cache = AsyncMock(return_value=cached_result)

        response = app_client.post('/simple_predict', json={'item_id': item_id})
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["is_violation"] == True
        assert response_data["probability"] == 0.95
        
        mock_ad_repo_instance.check_cache.assert_called_once_with(item_id)
        mock_ad_repo_instance.get.assert_not_called()
        mock_ad_repo_instance.to_cache.assert_not_called()


async def test_simple_predict_advertisement_not_found(app_client):
    data = {
        'item_id': 9999
    }
   
    response = app_client.post('/simple_predict', json=data)
    
    assert response.status_code == 404
    assert "Объявление не найдено" in response.json()["detail"]
    

async def test_simple_predict_user_not_found(app_client):
    item_id = 9999
    ad_repo = AdvertisementRepository()
    with pytest.raises(AdvertisementCreationError):
        advertisement = await ad_repo.create(
            item_id=item_id,
            seller_id=9999,
            name="Test Item",
            description="desc",
            category=10,
            images_qty=5
        )
        