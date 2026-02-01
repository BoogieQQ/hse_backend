import asyncpg
from typing import Mapping, Any, Sequence
from dataclasses import dataclass
from errors import AdvertisementNotFoundError, UserNotFoundError, AdvertisementCreationError
from schemas.simple_prediction import SimplePredictRequest, Advertisement
from clients.postgres import get_pg_connection


@dataclass(frozen=True)
class AdvertisementPostgresStorage:    
    async def create(self, item_id: int, seller_id: int, name: str, 
                     description: str, category: int, images_qty: int):
        query = '''
            INSERT INTO advertisements 
            (item_id, seller_id, name, description, category, images_qty)
            VALUES ($1::INTEGER, $2::INTEGER, $3::TEXT, $4::TEXT, $5::INTEGER, $6::INTEGER)
            RETURNING *
        '''
        
        async with get_pg_connection() as connection:
            try:
                row = await connection.fetchrow(query, item_id, seller_id, name, 
                                            description, category, images_qty)
                return dict(row)
            except Exception:
                raise AdvertisementCreationError('Не удалось создать объявление.')
    
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
class AdvertisementRepository:
    advertisement_postgres_storage: AdvertisementPostgresStorage = AdvertisementPostgresStorage()

    async def create(self, item_id: int, seller_id: int, name: str, description: str, category: int, images_qty: int):
        raw_advertisement = await self.advertisement_postgres_storage.create(item_id, seller_id, name, description, category, images_qty)
        return Advertisement(**raw_advertisement)

    async def get(self, item_id: int):
        raw_advertisement = await self.advertisement_postgres_storage.select(item_id)
        return Advertisement(**raw_advertisement)

    async def delete(self, item_id: int):
        raw_advertisement = await self.advertisement_postgres_storage.delete(item_id)
        return Advertisement(**raw_advertisement)
