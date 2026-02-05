import pytest
import asyncio
from errors import AdvertisementNotFoundError, UserNotFoundError
from repositories.users import UserPostgresStorage
from repositories.advertisements import AdvertisementPostgresStorage

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