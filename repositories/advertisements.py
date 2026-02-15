import asyncpg
from typing import Mapping, Any, Sequence
from dataclasses import dataclass
from errors import AdvertisementNotFoundError, UserNotFoundError, AdvertisementCreationError
from schemas.simple_prediction import SimplePredictRequest, Advertisement
from schemas.prediction import PredictionResponse
from clients.postgres import get_pg_connection
from clients.redis import get_redis_connection
from datetime import timedelta
from json import loads, dumps


@dataclass(frozen=True)
class AdvertisementPostgresStorage:    
    async def create(self, item_id: int, seller_id: int, name: str, 
                     description: str, category: int, images_qty: int, is_closed: bool = False):
        query = '''
            INSERT INTO advertisements 
            (item_id, seller_id, name, description, category, images_qty, is_closed)
            VALUES ($1::INTEGER, $2::INTEGER, $3::TEXT, $4::TEXT, $5::INTEGER, $6::INTEGER, $7::BOOLEAN)
            RETURNING *
        '''
        
        async with get_pg_connection() as connection:
            try:
                row = await connection.fetchrow(query, item_id, seller_id, name, 
                                            description, category, images_qty, is_closed)
                return dict(row)
            except Exception as e:
                raise AdvertisementCreationError(str(e))
    
    async def select(self, item_id: int):
        query = '''
            SELECT *
            FROM advertisements 
            WHERE item_id = $1::INTEGER
            LIMIT 1
        '''
        
        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, item_id)
            
            if row:
                return dict(row)
            
            raise AdvertisementNotFoundError('Не найдено объявление.')

    async def exists(self, item_id: int) -> bool:
        query = '''
            SELECT EXISTS(
                SELECT 1 
                FROM advertisements 
                WHERE item_id = $1::INTEGER
            )
        '''
        
        async with get_pg_connection() as connection:
            result = await connection.fetchval(query, item_id)
            return bool(result)
    
    async def delete(self, item_id: int):
        query = '''
            DELETE FROM advertisements
            WHERE item_id = $1::INTEGER
            RETURNING *
        '''
        
        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, item_id)
            
            if row:
                return dict(row)
            
            raise AdvertisementNotFoundError('Не найдено объявление.')

@dataclass(frozen=True)
class AdvertisementRedisStorage:
    _TTL: timedelta = timedelta(minutes=30)

    async def set(self, item_id: int, row: Mapping[str, Any]) -> None:
        async with get_redis_connection() as connection:
            pipeline = connection.pipeline()
            pipeline.set(
                name=f"advertisement:item:{str(item_id)}",
                value=dumps(row),
            )
            pipeline.expire(f"advertisement:item:{str(item_id)}", self._TTL)
            await pipeline.execute()
    
    async def get(self, item_id: int) -> Mapping[str, Any] | None:
        async with get_redis_connection() as connection:
            row = await connection.get(f"advertisement:item:{str(item_id)}")

            if row:
                return loads(row)
            
            return None

    async def delete(self, item_id: int) -> None:
        async with get_redis_connection() as connection:
            await connection.delete(f"advertisement:item:{str(item_id)}")


@dataclass(frozen=True)
class AdvertisementRepository:
    advertisement_postgres_storage: AdvertisementPostgresStorage = AdvertisementPostgresStorage()
    advertisement_redis_storage:    AdvertisementRedisStorage = AdvertisementRedisStorage()

    async def create(self, item_id: int, seller_id: int, name: str, description: str, category: int, images_qty: int, is_closed: bool = False):
        raw_advertisement = await self.advertisement_postgres_storage.create(item_id, seller_id, name, description, category, images_qty, is_closed)
        return Advertisement(**raw_advertisement)

    async def check_cache(self, item_id: int):
        if cached_result := await self.advertisement_redis_storage.get(item_id):
            return PredictionResponse(**cached_result)
        
        return None

    async def to_cache(self, item_id: int, is_violation: bool, probability: float):
        await self.advertisement_redis_storage.set(item_id, row={'is_violation': is_violation, 'probability': probability})
        return None

    async def get(self, item_id: int):
        raw_advertisement = await self.advertisement_postgres_storage.select(item_id)
        return Advertisement(**raw_advertisement)

    async def exists(self, item_id: int):
        is_exist = await self.advertisement_postgres_storage.exists(item_id)
        return is_exist

    async def delete(self, item_id: int):
        await self.advertisement_redis_storage.delete(item_id)
        raw_advertisement = await self.advertisement_postgres_storage.delete(item_id)
        return Advertisement(**raw_advertisement)
