from dataclasses import dataclass
from errors import UserNotFoundError, UserNotCreationError
from schemas.simple_prediction import User
from clients.postgres import get_pg_connection
from metrcis_constants import QueryType, TableName
from utils import track_db_query

@dataclass(frozen=True)
class UserPostgresStorage:  
    @track_db_query(query_type=QueryType.CREATE, table=TableName.USERS)  
    async def create(self, seller_id: int, is_verified_seller: bool):
        query = '''
            INSERT INTO users (seller_id, is_verified_seller)
            VALUES ($1::INTEGER, $2::BOOLEAN)
            RETURNING *
        '''

        async with get_pg_connection() as connection:
            try:
                row = await connection.fetchrow(query, seller_id, is_verified_seller)

                return dict(row)
            except Exception as e:
                raise UserNotCreationError(str(e))
    
    @track_db_query(query_type=QueryType.SELECT, table=TableName.USERS)  
    async def select(self, seller_id: int):
        query = '''
            SELECT *
            FROM users 
            WHERE seller_id = $1::INTEGER
            LIMIT 1
        '''

        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, seller_id)

            if row:
                return dict(row)
            
            raise UserNotFoundError('Не найден пользователь.')
    
    @track_db_query(query_type=QueryType.DELETE, table=TableName.USERS)  
    async def delete(self, seller_id: int):
        query = '''
            DELETE FROM users
            WHERE seller_id = $1::INTEGER
            RETURNING *
        '''

        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, seller_id)
            
            if row:
                return dict(row)
            
            raise UserNotFoundError('Не найден пользователь.')

@dataclass(frozen=True)
class UserRepository:
    user_postgres_storage: UserPostgresStorage = UserPostgresStorage()

    async def create(self, seller_id: int, is_verified_seller: bool):
        raw_user = await self.user_postgres_storage.create(seller_id, is_verified_seller)
        return User(**raw_user)

    async def get(self, user_id: int):
        raw_user = await self.user_postgres_storage.select(user_id)
        return User(**raw_user)

    async def delete(self, user_id: int):
        raw_user = await self.user_postgres_storage.delete(user_id)
        return User(**raw_user)
