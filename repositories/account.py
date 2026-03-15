import asyncpg
from typing import Mapping, Any, Optional
from dataclasses import dataclass
from errors import AccountNotFoundError, AccountCreationError, AccountBlockedError
from schemas.account import Account
from clients.postgres import get_pg_connection
from clients.redis import get_redis_connection
from datetime import timedelta
from json import loads, dumps
import time
from metrics import DB_QUERY_DURATION
import hashlib
import hmac


@dataclass(frozen=True)
class AccountPostgresStorage:
    async def create(self, login: str, password: str) -> Mapping[str, Any]:
        query = '''
            INSERT INTO account 
            (login, password, is_blocked)
            VALUES ($1::TEXT, $2::TEXT, $3::BOOLEAN)
            RETURNING id, login, password, is_blocked
        '''

        start_time = time.time()
        async with get_pg_connection() as connection:
            try:
                row = await connection.fetchrow(query, login, password, False)
                duration = time.time() - start_time

                DB_QUERY_DURATION.labels(query_type="create", table="account").observe(duration)
                
                if row:
                    return dict(row)
                raise AccountCreationError("Не удалось создать аккаунт")
            except Exception as e:
                raise AccountCreationError(str(e))
    
    async def select_by_id(self, account_id: int) -> Mapping[str, Any]:
        query = '''
            SELECT id, login, password, is_blocked
            FROM account 
            WHERE id = $1::INTEGER
            LIMIT 1
        '''

        start_time = time.time()
        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, account_id)
            duration = time.time() - start_time

            DB_QUERY_DURATION.labels(query_type="select_by_id", table="account").observe(duration)
            
            if row:
                return dict(row)
            
            raise AccountNotFoundError(f'Аккаунт с ID {account_id} не найден.')
    
    async def select_by_login(self, login: str) -> Mapping[str, Any]:
        query = '''
            SELECT id, login, password, is_blocked
            FROM account 
            WHERE login = $1::TEXT
            LIMIT 1
        '''

        start_time = time.time()
        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, login)
            duration = time.time() - start_time

            DB_QUERY_DURATION.labels(query_type="select_by_login", table="account").observe(duration)
            
            if row:
                return dict(row)
            
            raise AccountNotFoundError(f'Аккаунт с логином {login} не найден.')
    
    async def select_by_login_and_password(self, login: str, password: str) -> Mapping[str, Any]:
        query = '''
            SELECT id, login, password, is_blocked
            FROM account 
            WHERE login = $1::TEXT AND password = $2::TEXT
            LIMIT 1
        '''

        start_time = time.time()
        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, login, password)
            duration = time.time() - start_time

            DB_QUERY_DURATION.labels(query_type="select_by_credentials", table="account").observe(duration)
            
            if row:
                return dict(row)
            
            raise AccountNotFoundError('Неверный логин или пароль.')
    
    async def delete(self, account_id: int) -> Mapping[str, Any]:
        query = '''
            DELETE FROM account
            WHERE id = $1::INTEGER
            RETURNING id, login, password, is_blocked
        '''
        start_time = time.time()
        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, account_id)
            duration = time.time() - start_time

            DB_QUERY_DURATION.labels(query_type="delete", table="account").observe(duration)
            
            if row:
                return dict(row)
            
            raise AccountNotFoundError(f'Аккаунт с ID {account_id} не найден.')
    
    async def block(self, account_id: int) -> Mapping[str, Any]:
        query = '''
            UPDATE account
            SET is_blocked = true
            WHERE id = $1::INTEGER
            RETURNING id, login, password, is_blocked
        '''
        start_time = time.time()
        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, account_id)
            duration = time.time() - start_time

            DB_QUERY_DURATION.labels(query_type="block", table="account").observe(duration)
            
            if row:
                return dict(row)
            
            raise AccountNotFoundError(f'Аккаунт с ID {account_id} не найден.')
    
    async def unblock(self, account_id: int) -> Mapping[str, Any]:
        query = '''
            UPDATE account
            SET is_blocked = false
            WHERE id = $1::INTEGER
            RETURNING id, login, password, is_blocked
        '''
        start_time = time.time()
        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, account_id)
            duration = time.time() - start_time

            DB_QUERY_DURATION.labels(query_type="unblock", table="account").observe(duration)
            
            if row:
                return dict(row)
            
            raise AccountNotFoundError(f'Аккаунт с ID {account_id} не найден.')
    
    async def exists(self, account_id: int) -> bool:
        query = '''
            SELECT EXISTS(
                SELECT 1 
                FROM account 
                WHERE id = $1::INTEGER
            )
        '''
        start_time = time.time()
        async with get_pg_connection() as connection:
            result = await connection.fetchval(query, account_id)
            duration = time.time() - start_time

            DB_QUERY_DURATION.labels(query_type="exists", table="account").observe(duration)
            return bool(result)
    
    async def exists_by_login(self, login: str) -> bool:
        query = '''
            SELECT EXISTS(
                SELECT 1 
                FROM account 
                WHERE login = $1::TEXT
            )
        '''
        start_time = time.time()
        async with get_pg_connection() as connection:
            result = await connection.fetchval(query, login)
            duration = time.time() - start_time

            DB_QUERY_DURATION.labels(query_type="exists_by_login", table="account").observe(duration)
            return bool(result)

@dataclass(frozen=True)
class AccountRepository:
    account_postgres_storage: AccountPostgresStorage = AccountPostgresStorage()

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    async def create(self, login: str, password: str) -> Account:
        hashed_password = self._hash_password(password)
        
        raw_account = await self.account_postgres_storage.create(login, hashed_password)
                
        return Account(**raw_account)

    async def get_by_id(self, account_id: int) -> Account:
        raw_account = await self.account_postgres_storage.select_by_id(account_id)
        
        return Account(**raw_account)

    async def get_by_login(self, login: str) -> Account:
        raw_account = await self.account_postgres_storage.select_by_login(login)
                
        return Account(**raw_account)

    async def get_by_login_and_password(self, login: str, password: str) -> Account:
        hashed_password = self._hash_password(password)
        
        raw_account = await self.account_postgres_storage.select_by_login_and_password(login, hashed_password)

        if raw_account['is_blocked']:
            raise AccountBlockedError(f'Аккаунт {login} заблокирован.')
        
        return Account(**raw_account)

    async def exists(self, account_id: int) -> bool:
        return await self.account_postgres_storage.exists(account_id)

    async def exists_by_login(self, login: str) -> bool:
        return await self.account_postgres_storage.exists_by_login(login)

    async def delete(self, account_id: int) -> Account:
        account = await self.get_by_id(account_id)
                
        raw_account = await self.account_postgres_storage.delete(account_id)
        
        return Account(**raw_account)

    async def block(self, account_id: int) -> Account:
        raw_account = await self.account_postgres_storage.block(account_id)
        
        return Account(**raw_account)

    async def unblock(self, account_id: int) -> Account:
        raw_account = await self.account_postgres_storage.unblock(account_id)
        
        return Account(**raw_account)
 