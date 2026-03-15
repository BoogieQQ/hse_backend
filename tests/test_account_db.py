import pytest
import asyncio
import hashlib
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Mapping, Any
from errors import AccountNotFoundError, AccountCreationError, AccountBlockedError
from schemas.account import Account
from repositories.account import AccountPostgresStorage, AccountRepository

IDS = [1, 100, 1000, 1_000_000]
LOGINS = ["user1", "test_user", "ivan", "123"]
PASSWORDS = ["password123", "aSDASDFSDFSDFS", "qwerty", "admin123"]


### ---------------------- ТЕСТЫ ТАБЛИЦЫ ACCOUNT ------------------------------------------
@pytest.fixture
def account_repository():
    return AccountRepository()

@pytest.mark.integration
@pytest.mark.parametrize('login,password', zip(LOGINS, PASSWORDS))
async def test_repository_create_account(account_repository, login, password):
    account = await account_repository.create(login, password)
    
    assert isinstance(account, Account)
    assert account.login == login
    assert account.is_blocked == False
    assert account.id > 0
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    raw_account = await account_repository.account_postgres_storage.select_by_id(account.id)
    assert raw_account['password'] == hashed_password
    assert raw_account['password'] != password
    
    await account_repository.delete(account.id)

@pytest.mark.integration
async def test_repository_create_account_with_duplicate_login(account_repository):
    login = "repo_duplicate_test"
    password = "test_pass"
    
    account1 = await account_repository.create(login, password)
    
    with pytest.raises(AccountCreationError) as exc_info:
        await account_repository.create(login, "different_pass")
    
    await account_repository.delete(account1.id)

@pytest.mark.integration
@pytest.mark.parametrize('account_id', IDS)
async def test_repository_get_account_by_id(account_repository, account_id):
    login = f"repo_get_{account_id}"
    password = f"pass_{account_id}"
    
    created = await account_repository.create(login, password)
    
    account = await account_repository.get_by_id(created.id)
    
    assert isinstance(account, Account)
    assert account.id == created.id
    assert account.login == login
    assert account.is_blocked == False
    
    await account_repository.delete(created.id)

@pytest.mark.integration
async def test_repository_get_account_by_id_not_found(account_repository):
    account_id = 999999
    
    with pytest.raises(AccountNotFoundError):
        await account_repository.get_by_id(account_id)

@pytest.mark.integration
@pytest.mark.parametrize('login,password', zip(LOGINS, PASSWORDS))
async def test_repository_get_account_by_login(account_repository, login, password):
    created = await account_repository.create(login, password)
    
    account = await account_repository.get_by_login(login)
    
    assert isinstance(account, Account)
    assert account.id == created.id
    assert account.login == login
    
    await account_repository.delete(created.id)

@pytest.mark.integration
async def test_repository_get_account_by_login_not_found(account_repository):
    login = "nonexistent_repo_login"
    
    with pytest.raises(AccountNotFoundError):
        await account_repository.get_by_login(login)

@pytest.mark.integration
@pytest.mark.parametrize('login,password', zip(LOGINS, PASSWORDS))
async def test_repository_get_account_by_credentials(account_repository, login, password):
    created = await account_repository.create(login, password)
    
    account = await account_repository.get_by_login_and_password(login, password)
    
    assert isinstance(account, Account)
    assert account.id == created.id
    assert account.login == login
    assert account.is_blocked == False
    
    await account_repository.delete(created.id)

@pytest.mark.integration
async def test_repository_get_account_by_wrong_password(account_repository):
    login = "repo_wrong_pass"
    password = "correct_pass"
    
    created = await account_repository.create(login, password)
    
    with pytest.raises(AccountNotFoundError):
        await account_repository.get_by_login_and_password(login, "wrong_pass")
    
    await account_repository.delete(created.id)

@pytest.mark.integration
async def test_repository_get_blocked_account_by_credentials(account_repository):
    login = "blocked_repo_test"
    password = "test_pass"
    
    created = await account_repository.create(login, password)
    
    await account_repository.block(created.id)
    
    with pytest.raises(AccountBlockedError) as exc_info:
        await account_repository.get_by_login_and_password(login, password)
    
    assert login in str(exc_info.value)
    
    await account_repository.delete(created.id)

@pytest.mark.integration
@pytest.mark.parametrize('account_id', IDS)
async def test_repository_delete_account(account_repository, account_id):
    login = f"repo_delete_{account_id}"
    password = f"pass_{account_id}"
    
    created = await account_repository.create(login, password)
    
    deleted = await account_repository.delete(created.id)
    
    assert isinstance(deleted, Account)
    assert deleted.id == created.id
    assert deleted.login == login
    
    with pytest.raises(AccountNotFoundError):
        await account_repository.get_by_id(created.id)

@pytest.mark.integration
async def test_repository_delete_account_not_found(account_repository):
    account_id = 999999
    
    with pytest.raises(AccountNotFoundError):
        await account_repository.delete(account_id)

@pytest.mark.integration
@pytest.mark.parametrize('account_id', IDS)
async def test_repository_block_and_unblock_account(account_repository, account_id):
    login = f"repo_block_{account_id}"
    password = f"pass_{account_id}"
    
    created = await account_repository.create(login, password)
    
    blocked = await account_repository.block(created.id)
    assert isinstance(blocked, Account)
    assert blocked.id == created.id
    assert blocked.is_blocked == True
    
    account = await account_repository.get_by_id(created.id)
    assert account.is_blocked == True
    
    unblocked = await account_repository.unblock(created.id)
    assert isinstance(unblocked, Account)
    assert unblocked.id == created.id
    assert unblocked.is_blocked == False
    
    account = await account_repository.get_by_id(created.id)
    assert account.is_blocked == False
    
    await account_repository.delete(created.id)

@pytest.mark.integration
async def test_repository_block_account_not_found(account_repository):
    account_id = 999999
    
    with pytest.raises(AccountNotFoundError):
        await account_repository.block(account_id)

@pytest.mark.integration
async def test_repository_unblock_account_not_found(account_repository):
    account_id = 999999
    
    with pytest.raises(AccountNotFoundError):
        await account_repository.unblock(account_id)

@pytest.mark.integration
@pytest.mark.parametrize('account_id', IDS)
async def test_account_exists(account_repository, account_id):
    login = f"repo_exists_{account_id}"
    password = f"pass_{account_id}"
    
    exists_before = await account_repository.exists(account_id)
    assert exists_before == False
    
    created = await account_repository.create(login, password)
    
    exists_after = await account_repository.exists(created.id)
    assert exists_after == True
    
    await account_repository.delete(created.id)
    
    exists_after_delete = await account_repository.exists(created.id)
    assert exists_after_delete == False

@pytest.mark.integration
@pytest.mark.parametrize('login', LOGINS)
async def test_account_exists_by_login(account_repository, login):
    password = "test_pass"
    
    exists_before = await account_repository.exists_by_login(login)
    assert exists_before == False
    
    created = await account_repository.create(login, password)
    
    exists_after = await account_repository.exists_by_login(login)
    assert exists_after == True
    
    await account_repository.delete(created.id)