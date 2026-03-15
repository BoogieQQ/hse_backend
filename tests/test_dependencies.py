import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import Request, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from freezegun import freeze_time

from dependencies import (
    get_current_user_optional,
    get_current_user_required,
    auth_service,
    account_repo,
    security
)
from schemas.account import Account
from errors import UnauthorizedError, AccountBlockedError


### ---------------------- ТЕСТЫ DEPENDENCIES ------------------------------------------

@pytest.fixture
def mock_auth_service():
    service = AsyncMock()
    service.verify = AsyncMock()
    return service

@pytest.fixture
def mock_account_repo():
    repo = AsyncMock()
    repo.get_by_id = AsyncMock()
    return repo

@pytest.fixture
def test_user():
    return Account(
        id=1,
        login="test_user",
        password_hash="hashed_password",
        is_blocked=False
    )

@pytest.fixture
def blocked_user():
    return Account(
        id=2,
        login="blocked_user",
        password_hash="hashed_password",
        is_blocked=True
    )

@pytest.fixture
def mock_request():
    request = MagicMock(spec=Request)
    request.cookies = {}
    return request

@pytest.fixture
def mock_credentials():
    credentials = MagicMock(spec=HTTPAuthorizationCredentials)
    credentials.credentials = "test_token_header"
    return credentials


### ---------------------- ТЕСТЫ get_current_user_optional ------------------------------------------

@pytest.mark.asyncio
async def test_get_current_user_optional_no_token(mock_request, mock_auth_service, mock_account_repo):
    mock_request.cookies = {}
    
    result = await get_current_user_optional(
        request=mock_request,
        credentials=None,
        auth_service=mock_auth_service,
        account_repo=mock_account_repo
    )
    
    assert result is None
    mock_auth_service.verify.assert_not_called()
    mock_account_repo.get_by_id.assert_not_called()

@pytest.mark.asyncio
async def test_get_current_user_optional_token_in_cookies_only(
    mock_request, mock_auth_service, mock_account_repo, test_user
):
    mock_request.cookies = {"x-user-token": "test_token_cookie"}
    mock_auth_service.verify.return_value = test_user.id
    mock_account_repo.get_by_id.return_value = test_user
    
    result = await get_current_user_optional(
        request=mock_request,
        credentials=None,
        auth_service=mock_auth_service,
        account_repo=mock_account_repo
    )
    
    assert result == test_user
    mock_auth_service.verify.assert_called_once_with("test_token_cookie")
    mock_account_repo.get_by_id.assert_called_once_with(test_user.id)

@pytest.mark.asyncio
async def test_get_current_user_optional_token_in_headers_only(
    mock_request, mock_credentials, mock_auth_service, mock_account_repo, test_user
):
    mock_request.cookies = {}
    mock_auth_service.verify.return_value = test_user.id
    mock_account_repo.get_by_id.return_value = test_user
    
    result = await get_current_user_optional(
        request=mock_request,
        credentials=mock_credentials,
        auth_service=mock_auth_service,
        account_repo=mock_account_repo
    )
    
    assert result == test_user
    mock_auth_service.verify.assert_called_once_with("test_token_header")
    mock_account_repo.get_by_id.assert_called_once_with(test_user.id)

@pytest.mark.asyncio
async def test_get_current_user_optional_both_tokens_cookies_priority(
    mock_request, mock_credentials, mock_auth_service, mock_account_repo, test_user
):
    mock_request.cookies = {"x-user-token": "test_token_cookie"}
    mock_auth_service.verify.return_value = test_user.id
    mock_account_repo.get_by_id.return_value = test_user
    
    result = await get_current_user_optional(
        request=mock_request,
        credentials=mock_credentials,
        auth_service=mock_auth_service,
        account_repo=mock_account_repo
    )
    
    assert result == test_user
    mock_auth_service.verify.assert_called_once_with("test_token_cookie")
    mock_account_repo.get_by_id.assert_called_once_with(test_user.id)

@pytest.mark.asyncio
async def test_get_current_user_optional_invalid_token(
    mock_request, mock_auth_service, mock_account_repo
):
    mock_request.cookies = {"x-user-token": "invalid_token"}
    mock_auth_service.verify.side_effect = UnauthorizedError("Невалидный токен")
    
    result = await get_current_user_optional(
        request=mock_request,
        credentials=None,
        auth_service=mock_auth_service,
        account_repo=mock_account_repo
    )
    
    assert result is None
    mock_account_repo.get_by_id.assert_not_called()

@pytest.mark.asyncio
async def test_get_current_user_optional_blocked_account(
    mock_request, mock_auth_service, mock_account_repo, blocked_user
):
    mock_request.cookies = {"x-user-token": "valid_token"}
    mock_auth_service.verify.return_value = blocked_user.id
    mock_account_repo.get_by_id.return_value = blocked_user
    
    result = await get_current_user_optional(
        request=mock_request,
        credentials=None,
        auth_service=mock_auth_service,
        account_repo=mock_account_repo
    )
    
    assert result is None
    mock_auth_service.verify.assert_called_once_with("valid_token")
    mock_account_repo.get_by_id.assert_called_once_with(blocked_user.id)

@pytest.mark.asyncio
async def test_get_current_user_optional_account_repo_raises_blocked(
    mock_request, mock_auth_service, mock_account_repo, test_user
):
    mock_request.cookies = {"x-user-token": "valid_token"}
    mock_auth_service.verify.return_value = test_user.id
    mock_account_repo.get_by_id.side_effect = AccountBlockedError()
    
    result = await get_current_user_optional(
        request=mock_request,
        credentials=None,
        auth_service=mock_auth_service,
        account_repo=mock_account_repo
    )
    
    assert result is None

### ---------------------- ТЕСТЫ get_current_user_required ------------------------------------------

@pytest.mark.asyncio
async def test_get_current_user_required_success(
    mock_request, mock_auth_service, mock_account_repo, test_user
):
    mock_request.cookies = {"x-user-token": "valid_token"}
    mock_auth_service.verify.return_value = test_user.id
    mock_account_repo.get_by_id.return_value = test_user
    
    result = await get_current_user_required(
        request=mock_request,
        credentials=None,
        auth_service=mock_auth_service,
        account_repo=mock_account_repo
    )
    
    assert result == test_user

@pytest.mark.asyncio
async def test_get_current_user_required_no_user(
    mock_request, mock_auth_service, mock_account_repo
):
    mock_request.cookies = {}
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_required(
            request=mock_request,
            credentials=None,
            auth_service=mock_auth_service,
            account_repo=mock_account_repo
        )
    
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Не авторизован"
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

@pytest.mark.asyncio
async def test_get_current_user_required_invalid_token(
    mock_request, mock_auth_service, mock_account_repo
):
    mock_request.cookies = {"x-user-token": "invalid_token"}
    mock_auth_service.verify.side_effect = UnauthorizedError("Невалидный токен")
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_required(
            request=mock_request,
            credentials=None,
            auth_service=mock_auth_service,
            account_repo=mock_account_repo
        )
    
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Не авторизован"

@pytest.mark.asyncio
async def test_get_current_user_required_blocked_account(
    mock_request, mock_auth_service, mock_account_repo, blocked_user
):
    mock_request.cookies = {"x-user-token": "valid_token"}
    mock_auth_service.verify.return_value = blocked_user.id
    mock_account_repo.get_by_id.return_value = blocked_user
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_required(
            request=mock_request,
            credentials=None,
            auth_service=mock_auth_service,
            account_repo=mock_account_repo
        )
    
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Не авторизован"
