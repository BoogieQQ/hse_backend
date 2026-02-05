import asyncpg
from typing import Mapping, Any, Sequence
from dataclasses import dataclass
from errors import ModerationResultNotFoundError, ModerationResultCreationError
from schemas.async_prediction import ModerationResult
from clients.postgres import get_pg_connection


@dataclass(frozen=True)
class ModerationResultPostgresStorage:    
    async def create(self, item_id: int, status: str, is_violation: bool = None, 
                     probability: float = None, error_message: str = None, 
                     processed_at: str = None, retry_count: int = None, 
                     max_retries: int = None):
        query = '''
            INSERT INTO moderation_results 
            (item_id, status, is_violation, probability, error_message, 
             processed_at, retry_count, max_retries)
            VALUES ($1::INTEGER, $2::VARCHAR, $3::BOOLEAN, $4::FLOAT, $5::TEXT, 
                    $6::TIMESTAMP, $7::INTEGER, $8::INTEGER)
            RETURNING *
        '''
        
        async with get_pg_connection() as connection:
            try:
                row = await connection.fetchrow(query, item_id, status, is_violation, 
                                            probability, error_message, processed_at, 
                                            retry_count, max_retries)
                return dict(row)
            except Exception as e:
                raise ModerationResultCreationError(str(e))
    
    async def select(self, task_id: int):
        query = '''
            SELECT *
            FROM moderation_results 
            WHERE id = $1::INTEGER
            LIMIT 1
        '''
        
        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, task_id)
            
            if row:
                return dict(row)
            
            raise ModerationResultNotFoundError('Не найден результат модерации.')
    
    async def exists(self, task_id: int) -> bool:
        query = '''
            SELECT EXISTS(
                SELECT 1 
                FROM moderation_results 
                WHERE id = $1::INTEGER
            )
        '''
        
        async with get_pg_connection() as connection:
            result = await connection.fetchval(query, task_id)
            return bool(result)
        
    async def delete(self, task_id: int):
        query = '''
            DELETE FROM moderation_results
            WHERE id = $1::INTEGER
            RETURNING *
        '''
        
        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, task_id)
            
            if row:
                return dict(row)
            
            raise ModerationResultNotFoundError('Не найден результат модерации.')


@dataclass(frozen=True)
class ModerationResultRepository:
    moderation_result_postgres_storage: ModerationResultPostgresStorage = ModerationResultPostgresStorage()

    async def create(self, item_id: int, status: str, is_violation: bool = None, 
                     probability: float = None, error_message: str = None, 
                     processed_at: str = None, retry_count: int = None, 
                     max_retries: int = None):
        raw_moderation_result = await self.moderation_result_postgres_storage.create(
            item_id, status, is_violation, probability, error_message, 
            processed_at, retry_count, max_retries
        )
        return ModerationResult(**raw_moderation_result)

    async def get(self, task_id: int):
        raw_moderation_result = await self.moderation_result_postgres_storage.select(task_id)
        return ModerationResult(**raw_moderation_result)

    async def exists(self, task_id: int):
        is_exist = await self.moderation_result_postgres_storage.exists(task_id)
        return is_exist

    async def delete(self, task_id: int):
        raw_moderation_result = await self.moderation_result_postgres_storage.delete(task_id)
        return ModerationResult(**raw_moderation_result)