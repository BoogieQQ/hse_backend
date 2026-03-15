import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from freezegun import freeze_time
from routes.auth import auth_router, auth_service
from schemas.account import AccountLogin, TokenResponse
from fastapi.responses import Response
from fastapi import HTTPException

from services.auth_service import AuthService
from schemas.account import Account
from errors import UserNotFoundError, UnauthorizedError, AuthorizedError, AccountBlockedError


### ---------------------- ТЕСТЫ СЕРВИСА АВТОРИЗАЦИИ ------------------------------------------

@pytest.fixture
def auth_service():
    service = AuthService()
    service.account_repo = AsyncMock()
    service.auth_repo = AsyncMock()
    return service

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


### ---------------------- ТЕСТЫ МЕТОДА LOGIN ------------------------------------------

@pytest.mark.asyncio
async def test_login_success(auth_service, test_user):
    auth_service.account_repo.get_by_login_and_password = AsyncMock(return_value=test_user)
    auth_service.auth_repo.update_refresh_token = AsyncMock()
    
    access_token, refresh_token = await auth_service.login("test_user", "password")
    
    assert access_token is not None
    assert refresh_token is not None
    auth_service.auth_repo.update_refresh_token.assert_called_once_with(
        user_id=test_user.id,
        new_refresh_token=refresh_token,
        ttl=auth_service._REFRESH_USER_TOKEN_TTL,
    )

@pytest.mark.asyncio
async def test_login_wrong_credentials(auth_service):
    auth_service.account_repo.get_by_login_and_password = AsyncMock(
        side_effect=UserNotFoundError()
    )
    
    with pytest.raises(AuthorizedError) as exc_info:
        await auth_service.login("wrong_user", "wrong_pass")
    
    assert "Неверный логин или пароль" in str(exc_info.value)

@pytest.mark.asyncio
async def test_login_blocked_account(auth_service, blocked_user):
    auth_service.account_repo.get_by_login_and_password = AsyncMock(return_value=blocked_user)
    
    with pytest.raises(AuthorizedError) as exc_info:
        await auth_service.login("blocked_user", "password")
    
    assert "Аккаунт заблокирован" in str(exc_info.value)
    auth_service.auth_repo.update_refresh_token.assert_not_called()

@pytest.mark.asyncio
async def test_login_account_repo_returns_blocked_error(auth_service):
    auth_service.account_repo.get_by_login_and_password = AsyncMock(
        side_effect=AccountBlockedError()
    )
    
    # Проверка исключения
    with pytest.raises(AuthorizedError) as exc_info:
        await auth_service.login("blocked_user", "password")
    
    assert "Аккаунт заблокирован" in str(exc_info.value)
    auth_service.auth_repo.update_refresh_token.assert_not_called()


### ---------------------- ТЕСТЫ МЕТОДА REFRESH_TOKEN ------------------------------------------

@pytest.mark.asyncio
async def test_refresh_token_success(auth_service, test_user):
    old_refresh_token = "old_refresh_token"
    
    auth_service.auth_repo.get_user_id_by_refresh_token = AsyncMock(return_value=test_user.id)
    auth_service.account_repo.get_by_id = AsyncMock(return_value=test_user)
    auth_service.auth_repo.update_refresh_token = AsyncMock()
    
    access_token, refresh_token = await auth_service.refresh_token(old_refresh_token)
    
    assert access_token is not None
    assert refresh_token is not None
    auth_service.auth_repo.update_refresh_token.assert_called_once_with(
        user_id=test_user.id,
        new_refresh_token=refresh_token,
        ttl=auth_service._REFRESH_USER_TOKEN_TTL,
        old_refresh_token=old_refresh_token,
    )

@pytest.mark.asyncio
async def test_refresh_token_invalid_token(auth_service):
    auth_service.auth_repo.get_user_id_by_refresh_token = AsyncMock(return_value=None)
    
    with pytest.raises(AuthorizedError) as exc_info:
        await auth_service.refresh_token("invalid_token")
    
    assert "Невалидный refresh токен" in str(exc_info.value)
    auth_service.account_repo.get_by_id.assert_not_called()

@pytest.mark.asyncio
async def test_refresh_token_user_not_found(auth_service):
    old_refresh_token = "valid_token"
    user_id = 999
    
    auth_service.auth_repo.get_user_id_by_refresh_token = AsyncMock(return_value=user_id)
    auth_service.account_repo.get_by_id = AsyncMock(side_effect=UserNotFoundError())
    
    with pytest.raises(AuthorizedError) as exc_info:
        await auth_service.refresh_token(old_refresh_token)
    
    auth_service.auth_repo.update_refresh_token.assert_not_called()

@pytest.mark.asyncio
async def test_refresh_token_blocked_user(auth_service, blocked_user):
    old_refresh_token = "valid_token"
    
    auth_service.auth_repo.get_user_id_by_refresh_token = AsyncMock(return_value=blocked_user.id)
    auth_service.account_repo.get_by_id = AsyncMock(return_value=blocked_user)
    
    with pytest.raises(AuthorizedError) as exc_info:
        await auth_service.refresh_token(old_refresh_token)
    
    assert "Аккаунт заблокирован" in str(exc_info.value)
    auth_service.auth_repo.update_refresh_token.assert_not_called()


### ---------------------- ТЕСТЫ МЕТОДА VERIFY ------------------------------------------

@pytest.mark.asyncio
@freeze_time("2024-01-01 12:00:00")
async def test_verify_valid_token(auth_service, test_user):
    token = auth_service._build_access_token(test_user)
    
    user_id = await auth_service.verify(token)
    
    assert user_id == test_user.id

@pytest.mark.asyncio
@freeze_time("2024-01-02 12:00:01")
async def test_verify_expired_token(auth_service, test_user):
    with freeze_time("2024-01-01 12:00:00"):
        token = auth_service._build_access_token(test_user)
    
    with pytest.raises(UnauthorizedError) as exc_info:
        await auth_service.verify(token)
    
    assert "Токен истек" in str(exc_info.value)

@pytest.mark.asyncio
async def test_verify_malformed_token(auth_service):
    with pytest.raises(UnauthorizedError) as exc_info:
        await auth_service.verify("malformed.token.string")
    
    assert "Невалидный токен" in str(exc_info.value)

@pytest.mark.asyncio
async def test_verify_token_without_user_id(auth_service):
    payload = {
        "login": "test_user",
        "token_type": "access",
        "expired_at": (datetime.now() + timedelta(days=1)).isoformat(),
    }
    token = auth_service._build_token(payload)
    
    with pytest.raises(UnauthorizedError) as exc_info:
        await auth_service.verify(token)
    
    assert "Невалидный токен" in str(exc_info.value)

@pytest.mark.asyncio
async def test_verify_token_wrong_signature(auth_service):
    test_user = Account(id=1, login="test_user", password_hash="hash", is_blocked=False)
    
    with patch.object(auth_service, '_SECRET', 'different_secret'):
        token = auth_service._build_access_token(test_user)
    
    with pytest.raises(UnauthorizedError) as exc_info:
        await auth_service.verify(token)
    
    assert "Невалидный токен" in str(exc_info.value)


### ---------------------- ТЕСТЫ ПОСТРОЕНИЯ ТОКЕНОВ ------------------------------------------

@pytest.mark.asyncio
@freeze_time("2024-01-01 12:00:00")
async def test_build_access_token_structure(auth_service, test_user):
    token = auth_service._build_access_token(test_user)
    payload = auth_service._parse_token(token)
    
    assert payload["user_id"] == test_user.id
    assert payload["login"] == test_user.login
    assert payload["token_type"] == "access"
    assert payload["expired_at"] == "2024-01-02T12:00:00"  # +1 день

@pytest.mark.asyncio
@freeze_time("2024-01-01 12:00:00")
async def test_build_refresh_token_structure(auth_service, test_user):
    token = auth_service._build_refresh_token(test_user)
    payload = auth_service._parse_token(token)
    
    assert payload["user_id"] == test_user.id
    assert payload["login"] == test_user.login
    assert payload["token_type"] == "refresh"
    assert payload["expired_at"] == "2024-01-03T12:00:00"  # +2 дня


### ---------------------- ТЕСТЫ РОУТЕРА АВТОРИЗАЦИИ ------------------------------------------
@pytest.fixture
def mock_auth_service():
    with patch('routes.auth.auth_service') as mock:
        yield mock

@pytest.mark.asyncio
async def test_login_success(mock_auth_service):
    login_data = AccountLogin(login="test_user", password="test_pass")
    response = Response()
    
    mock_auth_service.login = AsyncMock(return_value=("access_token", "refresh_token"))
    
    from routes.auth import login
    result = await login(login_data, response)
    
    assert isinstance(result, TokenResponse)
    assert result.access_token == "access_token"
    assert result.refresh_token == "refresh_token"
    assert result.token_type == "bearer"
    
    assert response.headers.get("set-cookie") is not None
    assert "x-user-token=access_token" in str(response.headers)

@pytest.mark.asyncio
async def test_login_authorized_error(mock_auth_service):
    login_data = AccountLogin(login="test_user", password="wrong_pass")
    response = Response()
    
    mock_auth_service.login = AsyncMock(
        side_effect=AuthorizedError("Неверный логин или пароль")
    )
    
    from routes.auth import login
    
    with pytest.raises(HTTPException) as exc_info:
        await login(login_data, response)
    
    assert exc_info.value.status_code == 401
    assert "Неверный логин или пароль" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_login_internal_server_error(mock_auth_service):
    login_data = AccountLogin(login="test_user", password="test_pass")
    response = Response()
    
    mock_auth_service.login = AsyncMock(
        side_effect=Exception("Database connection error")
    )
    
    from routes.auth import login
    
    with pytest.raises(HTTPException) as exc_info:
        await login(login_data, response)
    
    assert exc_info.value.status_code == 500
    assert "Внутренняя ошибка сервера при авторизации" in str(exc_info.value.detail)