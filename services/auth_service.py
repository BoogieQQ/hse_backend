from dataclasses import dataclass
from typing import Mapping, Any
import jwt
from datetime import datetime, timedelta
from contextlib import suppress

from repositories.account import AccountRepository
from repositories.auth import AuthRepository
from schemas.account import Account
from errors import UserNotFoundError, UnauthorizedError, AuthorizedError, AccountBlockedError


class AuthService:
    account_repo: AccountRepository = AccountRepository()
    auth_repo: AuthRepository = AuthRepository()

    _SECRET = 'secret_for_token'
    _USER_TOKEN_TTL = timedelta(days=1)
    _REFRESH_USER_TOKEN_TTL = timedelta(days=2)

    async def login(self, login: str, password: str) -> tuple[str, str]:
        try:
            user = await self.account_repo.get_by_login_and_password(login, password)

            if user.is_blocked:
                raise AccountBlockedError()

            access_token = self._build_access_token(user)
            refresh_token = self._build_refresh_token(user)

            await self.auth_repo.update_refresh_token(
                user_id=user.id,
                new_refresh_token=refresh_token,
                ttl=self._REFRESH_USER_TOKEN_TTL,
            )

            return access_token, refresh_token
            
        except UserNotFoundError:
            raise AuthorizedError("Неверный логин или пароль")
        except AccountBlockedError:
            raise AuthorizedError("Аккаунт заблокирован")

    async def refresh_token(self, old_refresh_token: str) -> tuple[str, str]:
        user_id = await self.auth_repo.get_user_id_by_refresh_token(old_refresh_token)

        if not user_id:
            raise AuthorizedError("Невалидный refresh токен")
        
        try:
            user = await self.account_repo.get_by_id(user_id)
        except UserNotFoundError:
            raise AuthorizedError("Пользователь не найден")

        if user.is_blocked:
            raise AuthorizedError("Аккаунт заблокирован")

        access_token = self._build_access_token(user)
        refresh_token = self._build_refresh_token(user)

        await self.auth_repo.update_refresh_token(
            user_id=user.id,
            new_refresh_token=refresh_token,
            ttl=self._REFRESH_USER_TOKEN_TTL,
            old_refresh_token=old_refresh_token,
        )

        return access_token, refresh_token

    async def verify(self, access_token: str) -> int:
        user_payload = {}
        
        with suppress(Exception):
            user_payload = self._parse_token(access_token)
        
        if raw_expired_at := user_payload.get('expired_at', None):
            if datetime.fromisoformat(raw_expired_at) < datetime.now():
                raise UnauthorizedError("Токен истек")
        
        if user_id := user_payload.get('user_id', None):
            return user_id
        
        raise UnauthorizedError("Невалидный токен")

    def _build_refresh_token(self, user: Account) -> str:
        refresh_payload = dict(
            user_id=user.id,
            login=user.login,
            token_type='refresh',
            expired_at=(datetime.now() + self._REFRESH_USER_TOKEN_TTL).isoformat(),
        )
        return self._build_token(refresh_payload)
    
    def _build_access_token(self, user: Account) -> str:
        user_payload = dict(
            user_id=user.id,
            login=user.login,
            token_type='access',
            expired_at=(datetime.now() + self._USER_TOKEN_TTL).isoformat(),
        )
        return self._build_token(user_payload)

    def _build_token(self, payload: Mapping[str, Any]) -> str:
        return jwt.encode(
            payload=payload,
            key=self._SECRET,
            algorithm='HS256',
        )

    def _parse_token(self, token: str) -> Mapping[str, Any]:
        return jwt.decode(
            jwt=token,
            key=self._SECRET,
            algorithms=['HS256'],
        )