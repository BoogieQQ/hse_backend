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
                     processed_at: str = None):
        query = '''
            INSERT INTO moderation_results 
            (item_id, status, is_violation, probability, error_message, 
             processed_at)
            VALUES ($1::INTEGER, $2::VARCHAR, $3::BOOLEAN, $4::FLOAT, $5::TEXT, 
                    $6::TIMESTAMP)
            RETURNING *
        '''
        
        async with get_pg_connection() as connection:
            try:
                row = await connection.fetchrow(query, item_id, status, is_violation, 
                                            probability, error_message, processed_at)
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

    async def update(self, task_id: int, status: str, is_violation: bool, probability: float):

        query = '''
            UPDATE moderation_results 
            SET status = $1,
                is_violation = $2,
                probability = $3,
                processed_at = NOW()
                WHERE id = $4
            RETURNING *
        '''
        
        async with get_pg_connection() as connection:
                row = await connection.fetchrow(
                    query, status, is_violation, probability, task_id
                )
                if row:
                    result = dict(row)
                    if 'processed_at' in result:
                        result['processed_at'] = result['processed_at'].isoformat()
                    return result
        
        raise ModerationResultNotFoundError(f'Модерация с ID={task_id} не найдена')

    async def update_failed(self, task_id: int, status: str, error_message: str):

        query = '''
            UPDATE moderation_results 
            SET status = $1,
                error_message = $2,
                processed_at = NOW()
                WHERE id = $3
            RETURNING *
        '''
        
        async with get_pg_connection() as connection:
                row = await connection.fetchrow(
                    query, status, error_message, task_id
                )
                if row:
                    result = dict(row)
                    if 'processed_at' in result:
                        result['processed_at'] = result['processed_at'].isoformat()
                    return result
        
        raise ModerationResultNotFoundError(f'Модерация с ID={task_id} не найдена')
       
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

    async def truncate_table(self):
        query = '''
            TRUNCATE TABLE moderation_results RESTART IDENTITY CASCADE;
        '''
        
        async with get_pg_connection() as connection:
            try:
                await connection.execute(query)
            except Exception as e:
                raise Exception(f"Не получилось отчистить таблицу: {str(e)}")
        
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
                     processed_at: str = None):
        raw_moderation_result = await self.moderation_result_postgres_storage.create(
            item_id, status, is_violation, probability, error_message, 
            processed_at
        )
        return ModerationResult(**raw_moderation_result)

    async def get(self, task_id: int):
        raw_moderation_result = await self.moderation_result_postgres_storage.select(task_id)
        return ModerationResult(**raw_moderation_result)
    
    async def update_failed(self, task_id: int, status: str, error_message: str):
        raw_moderation_result = await self.moderation_result_postgres_storage.update_failed(
            task_id, status, error_message
        )
        return ModerationResult(**raw_moderation_result)
    
    async def update(self, task_id: int, status: str, is_violation: bool, probability: float):
        raw_moderation_result = await self.moderation_result_postgres_storage.update(
            task_id, status, is_violation, probability
        )
        return ModerationResult(**raw_moderation_result)

    async def exists(self, task_id: int):
        is_exist = await self.moderation_result_postgres_storage.exists(task_id)
        return is_exist

    async def truncate(self):
        await self.moderation_result_postgres_storage.truncate_table()

    async def delete(self, task_id: int):
        raw_moderation_result = await self.moderation_result_postgres_storage.delete(task_id)
        return ModerationResult(**raw_moderation_result)