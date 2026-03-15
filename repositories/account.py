from typing import Mapping, Any
from dataclasses import dataclass
from errors import AccountNotFoundError, AccountCreationError, AccountBlockedError
from schemas.account import Account
from clients.postgres import get_pg_connection
import hashlib
from metrcis_constants import QueryType, TableName
from typing import Any
from utils import track_db_query
from clients.redis import get_redis_connection
from datetime import timedelta
from json import loads, dumps

@dataclass(frozen=True)
class AccountPostgresStorage:
    @track_db_query(query_type=QueryType.CREATE, table=TableName.ACCOUNT)
    async def create(self, login: str, password: str) -> Mapping[str, Any]:
        query = '''
            INSERT INTO account 
            (login, password, is_blocked)
            VALUES ($1::TEXT, $2::TEXT, $3::BOOLEAN)
            RETURNING id, login, password, is_blocked
        '''

        async with get_pg_connection() as connection:
            try:
                row = await connection.fetchrow(query, login, password, False)
                
                if row:
                    return dict(row)
                raise AccountCreationError("Не удалось создать аккаунт")
            except Exception as e:
                raise AccountCreationError(str(e))
            
    @track_db_query(query_type=QueryType.SELECT, table=TableName.ACCOUNT)
    async def select_by_id(self, account_id: int) -> Mapping[str, Any]:
        query = '''
            SELECT id, login, password, is_blocked
            FROM account 
            WHERE id = $1::INTEGER
            LIMIT 1
        '''

        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, account_id)

            if row:
                return dict(row)
            
            raise AccountNotFoundError(f'Аккаунт с ID {account_id} не найден.')
    
    @track_db_query(query_type=QueryType.SELECT, table=TableName.ACCOUNT)
    async def select_by_login(self, login: str) -> Mapping[str, Any]:
        query = '''
            SELECT id, login, password, is_blocked
            FROM account 
            WHERE login = $1::TEXT
            LIMIT 1
        '''

        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, login)
            
            if row:
                return dict(row)
            
            raise AccountNotFoundError(f'Аккаунт с логином {login} не найден.')
    
    @track_db_query(query_type=QueryType.SELECT, table=TableName.ACCOUNT)
    async def select_by_login_and_password(self, login: str, password: str) -> Mapping[str, Any]:
        query = '''
            SELECT id, login, password, is_blocked
            FROM account 
            WHERE login = $1::TEXT AND password = $2::TEXT
            LIMIT 1
        '''

        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, login, password)

            if row:
                return dict(row)
            
            raise AccountNotFoundError('Неверный логин или пароль.')
        
    @track_db_query(query_type=QueryType.DELETE, table=TableName.ACCOUNT)
    async def delete(self, account_id: int) -> Mapping[str, Any]:
        query = '''
            DELETE FROM account
            WHERE id = $1::INTEGER
            RETURNING id, login, password, is_blocked
        '''
        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, account_id)

            if row:
                return dict(row)
            
            raise AccountNotFoundError(f'Аккаунт с ID {account_id} не найден.')
    
    @track_db_query(query_type=QueryType.UPDATE, table=TableName.ACCOUNT)
    async def block(self, account_id: int) -> Mapping[str, Any]:
        query = '''
            UPDATE account
            SET is_blocked = true
            WHERE id = $1::INTEGER
            RETURNING id, login, password, is_blocked
        '''
        
        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, account_id)

            if row:
                return dict(row)
            
            raise AccountNotFoundError(f'Аккаунт с ID {account_id} не найден.')
    
    @track_db_query(query_type=QueryType.UPDATE, table=TableName.ACCOUNT)
    async def unblock(self, account_id: int) -> Mapping[str, Any]:
        query = '''
            UPDATE account
            SET is_blocked = false
            WHERE id = $1::INTEGER
            RETURNING id, login, password, is_blocked
        '''
        
        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, account_id)
            
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
        
        async with get_pg_connection() as connection:
            result = await connection.fetchval(query, account_id)

            return bool(result)

    @track_db_query(query_type=QueryType.EXISTS, table=TableName.ACCOUNT)
    async def exists_by_login(self, login: str) -> bool:
        query = '''
            SELECT EXISTS(
                SELECT 1 
                FROM account 
                WHERE login = $1::TEXT
            )
        '''
        
        async with get_pg_connection() as connection:
            result = await connection.fetchval(query, login)

            return bool(result)

@dataclass(frozen=True)
class AccountRedisStorage:
    # 30 минут - это компромисс между актуальностью данных и нагрузкой на основную бд.
    _TTL: timedelta = timedelta(minutes=30)

    async def set_by_id(self, account_id: int, account_data: Mapping[str, Any]) -> None:
        async with get_redis_connection() as connection:
            pipeline = connection.pipeline()
            pipeline.set(
                name=f"account:id:{str(account_id)}",
                value=dumps(account_data),
            )
            pipeline.expire(f"account:id:{str(account_id)}", self._TTL)
            
            if 'login' in account_data:
                pipeline.set(
                    name=f"account:login:{account_data['login']}",
                    value=dumps(account_data),
                )
                pipeline.expire(f"account:login:{account_data['login']}", self._TTL)
            
            await pipeline.execute()
    
    async def get_by_id(self, account_id: int) -> Mapping[str, Any] | None:
        async with get_redis_connection() as connection:
            row = await connection.get(f"account:id:{str(account_id)}")

            if row:
                return loads(row)
            
            return None
    
    async def get_by_login(self, login: str) -> Mapping[str, Any] | None:
        async with get_redis_connection() as connection:
            row = await connection.get(f"account:login:{login}")

            if row:
                return loads(row)
            
            return None

    async def delete(self, account_id: int, login: str | None = None) -> None:
        async with get_redis_connection() as connection:
            pipeline = connection.pipeline()
            pipeline.delete(f"account:id:{str(account_id)}")
            
            if login:
                pipeline.delete(f"account:login:{login}")
            
            await pipeline.execute()


@dataclass(frozen=True)
class AccountRepository:
    account_postgres_storage: AccountPostgresStorage = AccountPostgresStorage()
    account_redis_storage: AccountRedisStorage = AccountRedisStorage()

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    async def create(self, login: str, password: str) -> Account:
        hashed_password = self._hash_password(password)
        
        raw_account = await self.account_postgres_storage.create(login, hashed_password)
    
        await self.account_redis_storage.set_by_id(raw_account['id'], raw_account)
        
        return Account(**raw_account)

    async def get_by_id(self, account_id: int) -> Account:
        cached_account = await self.account_redis_storage.get_by_id(account_id)
        if cached_account:
            return Account(**cached_account)
        
        raw_account = await self.account_postgres_storage.select_by_id(account_id)
        
        await self.account_redis_storage.set_by_id(account_id, raw_account)
        
        return Account(**raw_account)

    async def get_by_login(self, login: str) -> Account:
        cached_account = await self.account_redis_storage.get_by_login(login)
        if cached_account:
            return Account(**cached_account)
        
        raw_account = await self.account_postgres_storage.select_by_login(login)
        
        await self.account_redis_storage.set_by_id(raw_account['id'], raw_account)
        
        return Account(**raw_account)

    async def get_by_login_and_password(self, login: str, password: str) -> Account:
        hashed_password = self._hash_password(password)
        
        cached_account = await self.account_redis_storage.get_by_login(login)
        if cached_account and cached_account['password'] == hashed_password:
            if cached_account['is_blocked']:
                raise AccountBlockedError(f'Аккаунт {login} заблокирован.')
            return Account(**cached_account)
        
        raw_account = await self.account_postgres_storage.select_by_login_and_password(login, hashed_password)

        if raw_account['is_blocked']:
            raise AccountBlockedError(f'Аккаунт {login} заблокирован.')
        
        await self.account_redis_storage.set_by_id(raw_account['id'], raw_account)
        
        return Account(**raw_account)

    async def exists(self, account_id: int) -> bool:
        cached_account = await self.account_redis_storage.get_by_id(account_id)
        if cached_account:
            return True
        
        return await self.account_postgres_storage.exists(account_id)

    async def exists_by_login(self, login: str) -> bool:
        cached_account = await self.account_redis_storage.get_by_login(login)
        if cached_account:
            return True
        
        return await self.account_postgres_storage.exists_by_login(login)

    async def delete(self, account_id: int) -> Account:
        try:
            account = await self.get_by_id(account_id)
            login = account.login
        except AccountNotFoundError:
            login = None
        
        raw_account = await self.account_postgres_storage.delete(account_id)
        
        await self.account_redis_storage.delete(account_id, login)
        
        return Account(**raw_account)

    async def block(self, account_id: int) -> Account:
        raw_account = await self.account_postgres_storage.block(account_id)
        
        await self.account_redis_storage.set_by_id(account_id, raw_account)
        
        return Account(**raw_account)

    async def unblock(self, account_id: int) -> Account:
        raw_account = await self.account_postgres_storage.unblock(account_id)
        
        await self.account_redis_storage.set_by_id(account_id, raw_account)
        
        return Account(**raw_account)
