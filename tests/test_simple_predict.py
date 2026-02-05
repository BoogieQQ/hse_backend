import pytest

from fastapi.testclient import TestClient
from main import app
from http import HTTPStatus
from fastapi import HTTPException

from repositories.users import UserRepository
from repositories.advertisements import AdvertisementRepository
from repositories.users import UserRepository
from errors import AdvertisementNotFoundError, UserNotFoundError, AdvertisementCreationError

@pytest.fixture
def app_client():
    with TestClient(app) as client:
        yield client


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
async def test_simple_predict_success_cases(
    app_client,
    test_name,
    is_verified,
    images_qty,
    description,
    category
):
    seller_id = 1
    user_repo = UserRepository()
    user = await user_repo.create(seller_id=seller_id, is_verified_seller=is_verified)
    
    item_id = 1
    ad_repo = AdvertisementRepository()
    advertisement = await ad_repo.create(
        item_id=item_id,
        seller_id=seller_id,
        name=f"{test_name}",
        description=description,
        category=category,
        images_qty=images_qty
    )
    
    try:
        data = {
            'item_id': item_id
        }

        response = app_client.post('/simple_predict', json=data)
        
        is_violation = (is_verified == False) & (images_qty < 2)
        
        response_data = response.json()
        assert response_data["is_violation"] == is_violation
        assert 0.0 <= response_data["probability"] <= 1.0
        
    finally:
        await ad_repo.delete(seller_id)
        await user_repo.delete(item_id)


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
        